from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from tfm_airquality import config  # noqa: E402
from tfm_airquality import evaluate as ev  # noqa: E402
from tfm_airquality import model as md  # noqa: E402
from tfm_airquality import monitor as mon  # noqa: E402
from tfm_airquality import serve  # noqa: E402
from tfm_airquality import uncertainty as unc  # noqa: E402
from tfm_airquality import validate as val  # noqa: E402
from tfm_airquality import tracking as track  # noqa: E402
from tfm_airquality.clean import clean  # noqa: E402
from tfm_airquality.features import build_features  # noqa: E402
from tfm_airquality.load import load_airquality_data  # noqa: E402
from tfm_airquality.split import split_temporal  # noqa: E402
from tfm_airquality import report  # noqa: E402

# Hiperparametros seleccionados en la estacion 7 mediante busqueda con
# validacion cruzada temporal.
PARAMS_MODELO = dict(n_estimators=500, num_leaves=63, learning_rate=0.05,
                     random_state=42, verbose=-1)


def titulo(texto):
    print()
    print('=' * 72)
    print(texto)
    print('=' * 72)


def main(comparar=False):
    inicio = time.time()
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------------
    titulo('1-2. CARGA Y DATA CONTRACT')
    # -----------------------------------------------------------------------

    crudo = load_airquality_data()
    print(f'{len(crudo):,} filas | {crudo.index.min():%d/%m/%Y} '
          f'a {crudo.index.max():%d/%m/%Y}')

    informe_val = val.validate(crudo)
    print(informe_val)
    informe_val.raise_if_failed()

    # -----------------------------------------------------------------------
    titulo('3. LIMPIEZA')
    # -----------------------------------------------------------------------

    df, calidad = clean(crudo)
    calidad.to_csv(config.REPORTS_DIR / 'calidad_datos.csv', index=False)

    utiles = (df['objetivo_observado'] & df['entradas_completas']).sum()
    print(f'columnas descartadas : {config.UNUSABLE_COLUMNS}')
    print(f'horas utilizables    : {utiles:,} de {len(df):,}')
    print(f'valores interpolados : {int(df["n_estimados"].sum())}')

    from tfm_airquality import eda
    resumen = eda.exceedance_report(df)

    print()
    print('SUPERACIONES DEL LIMITE LEGAL')
    print(f'  superaciones     : {resumen["superaciones"]} '
          f'({resumen["pct_observadas"]} % de las horas observadas)')
    print(f'  episodios        : {resumen["episodios"]}')
    print(f'  duracion media   : {resumen["duracion_media"]} h')
    print(f'  duracion maxima  : {resumen["duracion_maxima"]} h')
    print(f'  media anual      : {resumen["media_anual"]} ug/m3')

    pd.DataFrame([resumen]).to_csv(
        config.REPORTS_DIR / 'superaciones.csv', index=False)

    # -----------------------------------------------------------------------
    titulo('5. CONSTRUCCION DE VARIABLES')
    # -----------------------------------------------------------------------

    tabla = build_features(df)
    cols = md.feature_columns(tabla, 'A')
    print(f'{len(tabla):,} filas ({len(config.HORIZONTES)} horizontes) '
          f'| {len(cols)} variables')

    # -----------------------------------------------------------------------
    titulo('6. PARTICION Y MODELOS DE REFERENCIA')
    # -----------------------------------------------------------------------

    train, test = split_temporal(tabla)
    print(f'train: {len(train):,} filas hasta {train.index.max():%d/%m/%Y}')
    print(f'test : {len(test):,} filas desde {test.index.min():%d/%m/%Y}')
    print(f'(embargo de 48 h entre ambos)')

    baselines = ev.evaluate_baselines(df[config.TARGET], test.index)
    liston = ev.best_baseline(baselines)
    liston.to_csv(config.REPORTS_DIR / 'baselines.csv')

    print()
    print('LISTON A BATIR')
    for h in config.HORIZONTES:
        f = liston.loc[h]
        print(f'  h={h:2d}: {f["MAE"]:6.2f}  ({f["mejor_baseline"]})')
    print(f'  media: {liston["MAE"].mean():.2f}')

    # -----------------------------------------------------------------------
    if comparar:
        titulo('7a. ESCALERA DE MODELOS (--comparar)')

        track.setup()
        comp = md.train_evaluate(train, test, escenario='A')
        pivote = comp.pivot(index='horizonte', columns='modelo', values='MAE')
        pivote.to_csv(config.REPORTS_DIR / 'comparacion.csv')

        modelos = md.build_models()
        for nombre in pivote.columns:
            metricas = {f'MAE_h{h}': float(pivote.loc[h, nombre])
                        for h in pivote.index}
            metricas['MAE_medio'] = float(pivote[nombre].mean())
            metricas['skill_medio'] = float(
                1 - pivote[nombre].mean() / liston['MAE'].mean()
            )

            track.log_model_run(
                nombre=nombre,
                modelo=modelos[nombre],
                params={'escenario': 'A', 'n_variables': len(cols),
                        'horizontes': str(list(config.HORIZONTES))},
                metricas=metricas,
                tags={'fase': 'comparacion', 'familia': nombre},
            )

        print(pivote.round(2).to_string())
        print()
        print('MAE medio por modelo:')
        for m, v in pivote.mean().sort_values().items():
            print(f'  {m:16s} {v:6.2f}')
        print()
        print('registrado en MLflow')

    # -----------------------------------------------------------------------
    titulo('7b. MODELO FINAL')
    # -----------------------------------------------------------------------

    tr = train[cols + ['y']].dropna()
    te = test[cols + ['y']].dropna()

    modelo = LGBMRegressor(**PARAMS_MODELO)
    modelo.fit(tr[cols], tr['y'])

    pred = modelo.predict(te[cols])
    metricas = []
    for h in sorted(te['horizonte'].unique()):
        m = (te['horizonte'] == h).to_numpy()
        mae = float(np.abs(te['y'].to_numpy()[m] - pred[m]).mean())
        metricas.append({'horizonte': h, 'MAE': round(mae, 2),
                         'liston': round(liston.loc[h, 'MAE'], 2),
                         'skill': round(1 - mae / liston.loc[h, 'MAE'], 3)})

    resumen = pd.DataFrame(metricas).set_index('horizonte')
    resumen.to_csv(config.REPORTS_DIR / 'modelo_final.csv')

    print(resumen.to_string())
    print()
    print(f'MAE medio: {resumen["MAE"].mean():.2f} '
          f'(liston {resumen["liston"].mean():.2f}, '
          f'mejora {resumen["skill"].mean():.1%})')

    track.setup()
    run_id = track.log_model_run(
        nombre='modelo_final',
        modelo=modelo,
        params={**PARAMS_MODELO, 'escenario': 'A', 'n_variables': len(cols)},
        metricas={
            **{f'MAE_h{h}': float(resumen.loc[h, 'MAE']) for h in resumen.index},
            'MAE_medio': float(resumen['MAE'].mean()),
            'skill_medio': float(resumen['skill'].mean()),
        },
        tags={'fase': 'final', 'seleccionado': 'si'},
    )
    print(f'registrado en MLflow: {run_id[:8]}')

    # -----------------------------------------------------------------------
    titulo('9-10. CALIBRACION Y PERSISTENCIA')
    # -----------------------------------------------------------------------

    # El modelo desplegado se entrena solo con el tramo de ajuste, para que los
    # errores de calibracion procedan de datos que no ha visto.
    ajuste, calib = unc.split_calibration(train)
    aj = ajuste[cols + ['y']].dropna()
    ca = calib[cols + ['y']].dropna()

    modelo_desplegado = LGBMRegressor(**PARAMS_MODELO)
    modelo_desplegado.fit(aj[cols], aj['y'])

    errores = (ca['y'] - modelo_desplegado.predict(ca[cols])).to_numpy()
    horizontes_cal = ca['horizonte'].to_numpy()

    print(f'ajuste      : {len(aj):,} filas')
    print(f'calibracion : {len(ca):,} filas')
    print()
    print('SEMIANCHURA DEL INTERVALO')
    for h, w in sorted(unc.conformal_width_by_horizon(errores,
                                                      horizontes_cal).items()):
        print(f'  h={h:2d}: +/-{w:.1f}')

    serve.save_model(modelo_desplegado, cols, errores, horizontes_cal)
    print()
    print(f'modelo guardado en {config.MODELS_DIR}')

    # -----------------------------------------------------------------------
    titulo('11. MONITORIZACION')
    # -----------------------------------------------------------------------

    deriva = mon.drift_report(train, test)
    deriva.to_csv(config.REPORTS_DIR / 'deriva.csv', index=False)
    print(deriva.to_string(index=False))

    resultado = serve.predict(te[cols])
    resultado['real'] = te['y'].values
    rend = mon.performance_report(resultado['real'], resultado['prediccion'],
                                  resultado['inferior'], resultado['superior'])

    print()
    print('RENDIMIENTO MES A MES')
    print(rend.to_string())

    avisos = mon.check_alerts(deriva, rend, float(np.abs(errores).mean()))
    if len(avisos):
        print()
        print('ALARMAS')
        print(avisos.to_string(index=False))

        # -----------------------------------------------------------------------
    titulo('CIFRAS DE LA MEMORIA')
    # -----------------------------------------------------------------------

    cifras = []
    cifras += report.calidad_del_dato(crudo, df)
    cifras += report.benceno(crudo)
    cifras += report.patrones(df)
    cifras += report.superaciones(df)
    cifras += report.correlaciones(df)
    cifras += report.desgaste(df)
    cifras += report.variables(df, tabla, cols)
    cifras += report.evaluacion(df, train, test)
    cifras += report.modelos(liston, resumen,
                             pivote if comparar else None)

    anchuras = unc.conformal_width_by_horizon(errores, horizontes_cal)
    dentro = ((resultado['real'] >= resultado['inferior']) &
              (resultado['real'] <= resultado['superior']))
    cobertura_h = dentro.groupby(te['horizonte'].values).mean().to_dict()
    cifras += report.incertidumbre(anchuras, cobertura_h)

    cifras += report.monitorizacion(deriva, rend)

    ruta_csv, ruta_txt = report.guardar(cifras)
    print(f'{len(cifras)} cifras registradas')
    print(f'  -> {ruta_csv.name}')
    print(f'  -> {ruta_txt.name}')

    # -----------------------------------------------------------------------
    titulo(f'PIPELINE COMPLETADO EN {time.time() - inicio:.0f} SEGUNDOS')
    # -----------------------------------------------------------------------

    print(f'informes en {config.REPORTS_DIR}')
    print(f'modelo   en {config.MODELS_DIR}')
    print()
    print('Para levantar el servicio:')
    print('  uvicorn tfm_airquality.api:app')
    print('  streamlit run app.py')

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comparar', action='store_true',
                        help='entrena tambien la escalera de modelos')
    args = parser.parse_args()

    raise SystemExit(main(comparar=args.comparar))