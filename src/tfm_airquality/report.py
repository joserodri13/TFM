from __future__ import annotations

import numpy as np
import pandas as pd

from tfm_airquality import config
from tfm_airquality.clean import gap_runs


def _fila(apartado, concepto, valor, unidad=''):
    return {'apartado': apartado, 'concepto': concepto,
            'valor': valor, 'unidad': unidad}


# ---------------------------------------------------------------------------
# 3.2 Calidad del dato
# ---------------------------------------------------------------------------

def calidad_del_dato(crudo, limpio):
    """Cifras del apartado 3.2: ausentes, paradas y ciclo de calibracion."""
    f = []

    ausentes = int((crudo == config.MISSING_SENTINEL).sum().sum())
    celdas = crudo.size
    f.append(_fila('3.2', 'celdas con marcador -200', ausentes))
    f.append(_fila('3.2', 'porcentaje de celdas ausentes',
                   round(100 * ausentes / celdas, 1), '%'))

    for col in [config.TARGET, 'CO(GT)', 'NOx(GT)', 'NMHC(GT)', 'C6H6(GT)']:
        if col not in limpio.columns and col not in crudo.columns:
            continue
        serie = crudo[col].replace(config.MISSING_SENTINEL, np.nan)
        f.append(_fila('3.2', f'ausentes en {col}', int(serie.isna().sum())))
        f.append(_fila('3.2', f'porcentaje ausente en {col}',
                       round(100 * serie.isna().mean(), 1), '%'))

    # Paradas del analizador en la variable objetivo
    serie = crudo[config.TARGET].replace(config.MISSING_SENTINEL, np.nan)
    rachas = gap_runs(serie)
    largas = rachas[rachas['horas'] >= 12]
    cortas = rachas[rachas['horas'] == 1]

    f.append(_fila('3.2', 'paradas de 12 h o mas en NO2', len(largas)))
    f.append(_fila('3.2', 'horas perdidas en esas paradas',
                   int(largas['horas'].sum())))
    f.append(_fila('3.2', 'porcentaje del dato perdido en paradas largas',
                   round(100 * largas['horas'].sum() / rachas['horas'].sum()), '%'))
    f.append(_fila('3.2', 'parada mas larga', int(rachas['horas'].max()), 'h'))
    f.append(_fila('3.2', 'paradas de una sola hora', len(cortas)))

    # Ciclo de autocalibracion: hora del dia de las paradas de 1 h
    horas = cortas['inicio'].dt.hour.value_counts()
    if len(horas):
        f.append(_fila('3.2', 'paradas de 1 h a las 03:00',
                       int(horas.get(3, 0))))
    f.append(_fila('3.2', 'filas totales', len(crudo)))
    f.append(_fila('3.2', 'horas entre primer y ultimo registro',
                   int((crudo.index.max() - crudo.index.min()).total_seconds() / 3600) + 1))

    return f


# ---------------------------------------------------------------------------
# 3.2 El benceno
# ---------------------------------------------------------------------------

def benceno(crudo):
    """Indicios de que C6H6(GT) es una transformacion de PT08.S2."""
    f = []
    d = crudo[['C6H6(GT)', 'PT08.S2(NMHC)']].replace(
        config.MISSING_SENTINEL, np.nan).dropna()

    f.append(_fila('3.2', 'correlacion C6H6 con PT08.S2',
                   round(float(d['C6H6(GT)'].corr(d['PT08.S2(NMHC)'])), 3)))
    f.append(_fila('3.2', 'valores distintos de C6H6', int(d['C6H6(GT)'].nunique())))
    f.append(_fila('3.2', 'valores distintos de PT08.S2',
                   int(d['PT08.S2(NMHC)'].nunique())))

    # Correspondencia univoca: cuantos valores del sensor tienen un unico
    # valor de benceno asociado
    g = d.groupby('PT08.S2(NMHC)')['C6H6(GT)'].nunique()
    f.append(_fila('3.2', 'valores del sensor con un unico benceno asociado',
                   int((g == 1).sum())))
    f.append(_fila('3.2', 'valores del sensor evaluados', len(g)))

    return f


# ---------------------------------------------------------------------------
# 4.1 Patrones temporales
# ---------------------------------------------------------------------------

def patrones(limpio):
    """Perfiles horario y semanal del apartado 4.1."""
    f = []
    y = limpio[config.TARGET]

    horario = y.groupby(limpio.index.hour).mean()
    f.append(_fila('4.1', 'minimo horario',
                   round(float(horario.min()), 1), 'ug/m3'))
    f.append(_fila('4.1', 'hora del minimo', int(horario.idxmin())))
    f.append(_fila('4.1', 'maximo horario',
                   round(float(horario.max()), 1), 'ug/m3'))
    f.append(_fila('4.1', 'hora del maximo', int(horario.idxmax())))

    dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado',
            'domingo']
    semanal = y.groupby(limpio.index.dayofweek).mean()
    for i, nombre in enumerate(dias):
        if i in semanal.index:
            f.append(_fila('4.1', f'media {nombre}',
                           round(float(semanal[i]), 1), 'ug/m3'))

    if 4 in semanal.index and 6 in semanal.index:
        f.append(_fila('4.1', 'domingo frente a viernes',
                       round(100 * (semanal[6] / semanal[4] - 1), 1), '%'))

    return f


# ---------------------------------------------------------------------------
# 4.2 Superaciones del limite legal
# ---------------------------------------------------------------------------

def superaciones(limpio):
    """Superaciones, episodios y estacionalidad del apartado 4.2."""
    f = []
    y = limpio[config.TARGET]
    observado = y.dropna()
    supera = observado > config.UMBRAL_LEGAL

    f.append(_fila('4.2', 'superaciones del limite horario', int(supera.sum())))
    f.append(_fila('4.2', 'porcentaje de horas observadas',
                   round(100 * supera.mean(), 1), '%'))
    f.append(_fila('4.2', 'superaciones permitidas por la norma', 18))
    f.append(_fila('4.2', 'veces por encima de lo permitido',
                   round(supera.sum() / 18, 1)))
    f.append(_fila('4.2', 'media anual', round(float(y.mean()), 1), 'ug/m3'))
    f.append(_fila('4.2', 'limite anual legal', config.UMBRAL_LEGAL_ANUAL
                   if hasattr(config, 'UMBRAL_LEGAL_ANUAL') else 40, 'ug/m3'))

    # Episodios: rachas de horas consecutivas por encima del umbral
    episodios = gap_runs(observado.where(~supera))
    if len(episodios):
        f.append(_fila('4.2', 'episodios de superacion', len(episodios)))
        f.append(_fila('4.2', 'duracion media del episodio',
                       round(float(episodios['horas'].mean()), 1), 'h'))
        f.append(_fila('4.2', 'duracion maxima del episodio',
                       int(episodios['horas'].max()), 'h'))
        f.append(_fila('4.2', 'episodios de una sola hora',
                       round(100 * (episodios['horas'] == 1).mean(), 0), '%'))

    # Distribucion horaria y mensual
    por_hora = supera.groupby(observado.index.hour).sum()
    madrugada = int(por_hora.reindex(range(3, 8)).fillna(0).sum())
    tarde = int(por_hora.reindex(range(18, 22)).fillna(0).sum())
    f.append(_fila('4.2', 'superaciones entre las 03:00 y las 07:00', madrugada))
    f.append(_fila('4.2', 'superaciones entre las 18:00 y las 21:00', tarde))
    f.append(_fila('4.2', 'porcentaje en la franja de tarde',
                   round(100 * tarde / supera.sum(), 0), '%'))

    por_mes = supera.groupby(observado.index.month).sum()
    for mes, n in por_mes.items():
        f.append(_fila('4.2', f'superaciones en el mes {mes:02d}', int(n)))
    f.append(_fila('4.2', 'porcentaje de superaciones en febrero',
                   round(100 * por_mes.get(2, 0) / supera.sum(), 0), '%'))

    return f


# ---------------------------------------------------------------------------
# 4.3 Correlaciones
# ---------------------------------------------------------------------------

def correlaciones(limpio):
    """Autocorrelacion y correlacion por horizonte del apartado 4.3."""
    f = []
    y = limpio[config.TARGET]

    for lag in [1, 6, 12, 24, 48, 168]:
        f.append(_fila('4.3', f'autocorrelacion a {lag} h',
                       round(float(y.autocorr(lag)), 3)))

    variables = [c for c in config.SENSOR_COLUMNS + config.MET_COLUMNS
                 if c in limpio.columns]
    for col in variables:
        f.append(_fila('4.3', f'correlacion {col} con NO2 (instante actual)',
                       round(float(limpio[col].corr(y)), 3)))
        for h in [6, 24, 48]:
            f.append(_fila('4.3', f'correlacion {col} con NO2 a h+{h}',
                           round(float(limpio[col].corr(y.shift(-h))), 3)))

    return f


# ---------------------------------------------------------------------------
# 4.4 Desgaste de los sensores
# ---------------------------------------------------------------------------

def desgaste(limpio):
    """Cociente concentracion/senal en marzo de 2004 y marzo de 2005."""
    f = []
    mes = limpio.index.to_period('M')

    for s in config.SENSOR_COLUMNS:
        if s not in limpio.columns:
            continue
        ratio = (limpio.groupby(mes)[config.TARGET].mean()
                 / limpio.groupby(mes)[s].mean()) * 1000

        m04 = pd.Period('2004-03', 'M')
        m05 = pd.Period('2005-03', 'M')
        if m04 in ratio.index and m05 in ratio.index:
            f.append(_fila('4.4', f'{s} cociente marzo 2004',
                           round(float(ratio[m04]), 1)))
            f.append(_fila('4.4', f'{s} cociente marzo 2005',
                           round(float(ratio[m05]), 1)))
            f.append(_fila('4.4', f'{s} variacion marzo a marzo',
                           round(100 * (ratio[m05] / ratio[m04] - 1), 0), '%'))

    return f


# ---------------------------------------------------------------------------
# 5.2 Variables construidas
# ---------------------------------------------------------------------------

def variables(limpio, tabla, columnas):
    """Recuento de variables y perdida de filas del apartado 5.2."""
    f = []

    utiles = int((limpio['objetivo_observado']
                  & limpio['entradas_completas']).sum())
    f.append(_fila('5.2', 'filas utiles tras la limpieza', utiles))

    completas = tabla[columnas + ['y']].dropna()
    por_h = completas.groupby('horizonte').size()
    f.append(_fila('5.2', 'filas completas por horizonte',
                   int(por_h.iloc[0]) if len(por_h) else 0))

    f.append(_fila('5.2', 'variables construidas', len(columnas)))
    f.append(_fila('5.2', 'retardos',
                   len([c for c in columnas if '_lag' in c])))
    f.append(_fila('5.2', 'estadisticos de ventana movil',
                   len([c for c in columnas if '_roll' in c])))
    f.append(_fila('5.2', 'variables de calendario',
                   len([c for c in columnas if c in
                        ['hora_sin', 'hora_cos', 'dia_sin', 'dia_cos',
                         'mes_sin', 'mes_cos', 'es_finde']])))

    return f


# ---------------------------------------------------------------------------
# 5.3 Estrategia de evaluacion
# ---------------------------------------------------------------------------

def evaluacion(limpio, train, test):
    """Particion, embargo y reparto de superaciones del apartado 5.3."""
    f = []

    f.append(_fila('5.3', 'fin del entrenamiento',
                   train.index.max().strftime('%d/%m/%Y %H:%M')))
    f.append(_fila('5.3', 'inicio del test',
                   test.index.min().strftime('%d/%m/%Y %H:%M')))
    f.append(_fila('5.3', 'embargo entre ambos',
                   int((test.index.min() - train.index.max()).total_seconds() / 3600),
                   'h'))

    y = limpio[config.TARGET]
    corte = config.FECHA_CORTE
    sup_train = int((y[y.index < corte] > config.UMBRAL_LEGAL).sum())
    sup_test = int((y[y.index >= corte] > config.UMBRAL_LEGAL).sum())

    f.append(_fila('5.3', 'superaciones en entrenamiento', sup_train))
    f.append(_fila('5.3', 'superaciones en test', sup_test))
    f.append(_fila('5.3', 'proporcion test/entrenamiento',
                   round(sup_test / sup_train, 1) if sup_train else None))

    return f


# ---------------------------------------------------------------------------
# 6 Modelos
# ---------------------------------------------------------------------------

def modelos(liston, resumen, comparacion=None):
    """Listón, escalera de modelos y resultado final del punto 6."""
    f = []

    for h in liston.index:
        f.append(_fila('6.1', f'mejor baseline h+{h}',
                       round(float(liston.loc[h, 'MAE']), 2), 'ug/m3'))
        f.append(_fila('6.1', f'metodo ganador h+{h}',
                       liston.loc[h, 'mejor_baseline']))
    f.append(_fila('6.1', 'MAE medio del liston',
                   round(float(liston['MAE'].mean()), 2), 'ug/m3'))

    if comparacion is not None:
        for m, v in comparacion.mean().sort_values().items():
            f.append(_fila('6.3', f'MAE medio de {m}', round(float(v), 2),
                           'ug/m3'))

    for h in resumen.index:
        f.append(_fila('6.3', f'MAE del modelo final h+{h}',
                       round(float(resumen.loc[h, 'MAE']), 2), 'ug/m3'))
        f.append(_fila('6.3', f'mejora sobre el liston h+{h}',
                       round(100 * float(resumen.loc[h, 'skill']), 1), '%'))

    f.append(_fila('6.3', 'MAE medio del modelo final',
                   round(float(resumen['MAE'].mean()), 2), 'ug/m3'))
    f.append(_fila('6.3', 'mejora media sobre el liston',
                   round(100 * float(resumen['skill'].mean()), 1), '%'))

    return f


# ---------------------------------------------------------------------------
# 8 Incertidumbre y alertas
# ---------------------------------------------------------------------------

def incertidumbre(anchuras, cobertura_por_h, alertas=None):
    """Anchuras de intervalo, cobertura y rendimiento de las alertas."""
    f = []

    for h, w in sorted(anchuras.items()):
        f.append(_fila('8.1', f'semianchura del intervalo h+{h}',
                       round(float(w), 1), 'ug/m3'))

    for h, c in sorted(cobertura_por_h.items()):
        f.append(_fila('8.1', f'cobertura real h+{h}',
                       round(100 * float(c), 1), '%'))
    f.append(_fila('8.1', 'cobertura nominal',
                   round(100 * config.COBERTURA), '%'))

    if alertas:
        for k, v in alertas.items():
            f.append(_fila('8.2', k, v))

    return f


# ---------------------------------------------------------------------------
# 10 Monitorizacion
# ---------------------------------------------------------------------------

def monitorizacion(deriva, rendimiento):
    """PSI por sensor y evolucion mensual del rendimiento."""
    f = []

    for _, fila in deriva.iterrows():
        f.append(_fila('10', f'PSI de {fila["variable"]}',
                       round(float(fila['PSI']), 3)))

    for periodo, fila in rendimiento.iterrows():
        etiqueta = periodo.strftime('%Y-%m')
        f.append(_fila('10', f'MAE en {etiqueta}',
                       round(float(fila['MAE']), 2), 'ug/m3'))
        f.append(_fila('10', f'cobertura en {etiqueta}',
                       round(100 * float(fila['cobertura']), 1), '%'))

    f.append(_fila('10', 'umbral PSI de alarma', config.PSI_MODERADO))
    f.append(_fila('10', 'umbral de cobertura minima',
                   round(100 * config.COBERTURA_MINIMA), '%'))

    return f


# ---------------------------------------------------------------------------
# Volcado
# ---------------------------------------------------------------------------

def guardar(filas, nombre='cifras_memoria'):
    """Escribe todas las cifras en un CSV y en un TXT legible."""
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(filas)

    ruta_csv = config.REPORTS_DIR / f'{nombre}.csv'
    df.to_csv(ruta_csv, index=False, sep=';', decimal=',',
              encoding='utf-8-sig')

    ruta_txt = config.REPORTS_DIR / f'{nombre}.txt'
    with open(ruta_txt, 'w', encoding='utf-8') as fh:
        fh.write('CIFRAS CITADAS EN LA MEMORIA\n')
        fh.write('=' * 72 + '\n')
        fh.write('Generado automaticamente por el pipeline.\n\n')

        for apartado in df['apartado'].unique():
            sub = df[df['apartado'] == apartado]
            fh.write(f'\n--- Apartado {apartado} ---\n')
            for _, r in sub.iterrows():
                unidad = f' {r["unidad"]}' if r['unidad'] else ''
                fh.write(f'  {r["concepto"]:<55s} {r["valor"]}{unidad}\n')

    return ruta_csv, ruta_txt