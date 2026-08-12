import numpy as np
import pandas as pd

from tfm_airquality import config

def add_lags(df, columnas, lags=(1, 24, 168)):
    """
    Añade columnas con retardos de las series horarias.

    df: tabla con un indice de fecha y hora y varias columnas de series horarias.
    columnas: lista de nombres de columnas a las que añadir retardos.
    lags: tupla de enteros positivos, cada uno indicando el numero de horas de retardo a añadir.
    Añade columnas con el valor de cada serie N horas antes.

    Solo usa información anterior a cada instante: `shift` con valores
    positivos nunca mira al futuro.
    """
    df = df.copy()
    for col in columnas:
        for lag in lags:
            df[f'{col}_lag{lag}'] = df[col].shift(lag)
    return df

def add_rolling(df, columnas, ventanas=(3, 24), funciones=('mean', 'std'),
                min_periods=None):
    """
    Añade medias y desviaciones de ventanas deslizantes hacia atrás.

    columnas: nombres de las columnas a procesar.
    ventanas: longitud de cada ventana, en horas.
    funciones: agregaciones a aplicar ('mean', 'std', 'min', 'max'...).
    min_periods: observaciones mínimas para calcular el valor. Por defecto,
        la mitad de la ventana: sin esto, un solo hueco anula la ventana
        completa, y con 1.642 horas ausentes en el objetivo eso descartaría
        una parte considerable del conjunto.

    `rolling` solo agrega valores anteriores o iguales a cada instante.
    """
    df = df.copy()
    for col in columnas:
        for ventana in ventanas:
            mp = min_periods if min_periods is not None else max(1, ventana // 2)
            for func in funciones:
                nombre = f'{col}_roll{ventana}_{func}'
                df[nombre] = df[col].rolling(ventana, min_periods=mp).agg(func)
    return df

def add_calendar(df):
    """
    Añade variables de calendario derivadas del índice temporal.

    Las variables cíclicas se codifican con seno y coseno para que valores
    contiguos del ciclo (las 23:00 y las 00:00) queden próximos en lugar de en
    extremos opuestos de la escala.

    Son las únicas variables conocidas de antemano para cualquier horizonte:
    no hay que predecir que el jueves que viene será jueves.
    """
    df = df.copy()

    hora = df.index.hour
    df['hora_sin'] = np.sin(2 * np.pi * hora / 24)
    df['hora_cos'] = np.cos(2 * np.pi * hora / 24)

    dia = df.index.dayofweek                      # 0 = lunes
    df['dia_sin'] = np.sin(2 * np.pi * dia / 7)
    df['dia_cos'] = np.cos(2 * np.pi * dia / 7)

    mes = df.index.month - 1                      # se resta 1 para que enero sea 0
    df['mes_sin'] = np.sin(2 * np.pi * mes / 12)
    df['mes_cos'] = np.cos(2 * np.pi * mes / 12)

    df['es_finde'] = (df.index.dayofweek >= 5).astype(int)

    return df

def build_features(df, horizontes=range(1, 49), lag_cols=None, roll_cols=None):
    """
    Construye la tabla lista para modelar.

    Devuelve una fila por cada combinación de instante y horizonte, con el
    horizonte como columna y el objetivo desplazado a t+h. Un único modelo
    sirve así para los 48 horizontes, en lugar de mantener 48 modelos.

    Las variables de entrada se calculan una sola vez: no dependen de h.
    """
    entradas = [c for c in config.SENSOR_COLUMNS + config.MET_COLUMNS
                if c in df.columns]
    lag_cols = lag_cols if lag_cols is not None else entradas + [config.TARGET]
    roll_cols = roll_cols if roll_cols is not None else entradas

    base = add_lags(df, lag_cols)
    base = add_rolling(base, roll_cols)
    base = add_calendar(base)

    # Los metadatos de calidad no son variables predictoras.
    base = base.drop(columns=[c for c in ['objetivo_observado',
                                          'entradas_completas', 'n_estimados']
                              if c in base.columns])

    bloques = []
    for h in horizontes:
        bloque = base.copy()
        bloque['horizonte'] = h
        # Único shift hacia el futuro del proyecto: es la respuesta a aprender,
        # no una entrada.
        bloque['y'] = df[config.TARGET].shift(-h)
        bloques.append(bloque)

    return pd.concat(bloques)
