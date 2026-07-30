import pandas as pd
import numpy as np
import tfm_airquality.load as load
import tfm_airquality.config as config

def sentinel_to_nan(df):
    """
    Convierte el marcador -200 en un hueco real (NaN).

    Primer paso de la limpieza y el más importante: hasta que el marcador no
    es un hueco, pandas lo trata como una medición válida.
    """
    return df.replace(config.MISSING_SENTINEL, np.nan)

def gap_runs(serie):
    """
    Localiza las rachas de huecos consecutivos de una serie.

    Devuelve una fila por racha, con su inicio, su fin y su longitud en horas,
    ordenadas de la más larga a la más corta. Es la pieza que permite
    distinguir una interrupción puntual de una parada del equipo.
    """
    es_nulo = serie.isna()

    if not es_nulo.any():
        return pd.DataFrame(columns=['inicio', 'fin', 'horas'])

    # Cada cambio de estado (dato -> hueco o hueco -> dato) abre un grupo
    # nuevo. Numerando esos cambios de forma acumulativa se obtiene un
    # identificador por tramo.
    grupos = (es_nulo != es_nulo.shift()).cumsum()

    aux = pd.DataFrame({
        'ts': serie.index[es_nulo],
        'grupo': grupos[es_nulo].to_numpy(),
    })

    rachas = aux.groupby('grupo')['ts'].agg(inicio='min', fin='max', horas='count')

    return rachas.reset_index(drop=True).sort_values('horas', ascending=False)

def interpolate_short_gaps(df, columnas, max_horas=config.MAX_INTERPOLABLE_GAP):
    """
    Interpola solo las rachas cuya longitud completa no supera el umbral.

    Devuelve la tabla y una tabla booleana que marca qué celdas son estimadas.
    """
    salida = df.copy()
    marcas = pd.DataFrame(False, index=df.index, columns=columnas)

    for col in columnas:
        rachas = gap_runs(df[col])
        cortas = rachas[rachas['horas'] <= max_horas] if len(rachas) else rachas
        if len(cortas) == 0:
            continue

        mascara = pd.Series(False, index=df.index)
        for _, racha in cortas.iterrows():
            mascara.loc[racha['inicio']:racha['fin']] = True

        # Se interpola la serie completa y solo después se copian los valores
        # autorizados: un hueco aislado no tiene vecinos con los que estimarse.
        estimada = df[col].interpolate(method='time', limit_area='inside')

        salida.loc[mascara, col] = estimada.loc[mascara]
        marcas.loc[mascara, col] = True

    return salida, marcas

def gap_report(df):
    """Resumen de huecos por columna: cuánto falta, en cuántas rachas y de qué longitud."""
    umbral = config.MAX_INTERPOLABLE_GAP
    filas = []

    for col in df.columns:
        rachas = gap_runs(df[col])
        cortas = rachas[rachas['horas'] <= umbral] if len(rachas) else rachas
        largas = rachas[rachas['horas'] > umbral] if len(rachas) else rachas

        filas.append({
            'columna': col,
            'n_ausentes': int(df[col].isna().sum()),
            'pct_ausentes': round(100 * df[col].isna().mean(), 2),
            'n_rachas': len(rachas),
            'n_cortas': len(cortas),
            'n_largas': len(largas),
            'horas_interpolables': int(cortas['horas'].sum()) if len(cortas) else 0,
            'horas_no_recuperables': int(largas['horas'].sum()) if len(largas) else 0,
            'racha_max': int(rachas['horas'].max()) if len(rachas) else 0,
        })

    return pd.DataFrame(filas).sort_values('pct_ausentes', ascending=False)


def add_quality_flags(df, marcas=None):
    """Añade metadatos de calidad por fila. No son variables predictoras."""
    salida = df.copy()

    salida['objetivo_observado'] = df[config.TARGET].notna()

    entradas = [c for c in config.SENSOR_COLUMNS + config.MET_COLUMNS
                if c in df.columns]
    salida['entradas_completas'] = df[entradas].notna().all(axis=1)

    if marcas is not None:
        salida['n_estimados'] = marcas.sum(axis=1).astype(int)
    else:
        salida['n_estimados'] = 0

    return salida


def clean(df):
    """
    Ejecuta la estación 3 completa.

    Devuelve la tabla limpia y el informe de huecos, calculado antes de
    interpolar para que describa el dato de origen.
    """
    df = sentinel_to_nan(df)

    # Se ha descartado la columna NMHC(GT) 
    descartar = [c for c in config.UNUSABLE_COLUMNS if c in df.columns]
    df = df.drop(columns=descartar)

    informe = gap_report(df)

    # El objetivo queda fuera: imputarlo sería inventar la respuesta correcta.
    entradas = [c for c in config.SENSOR_COLUMNS + config.MET_COLUMNS
                if c in df.columns]
    df, marcas = interpolate_short_gaps(df, entradas)

    df = add_quality_flags(df, marcas)

    return df, informe