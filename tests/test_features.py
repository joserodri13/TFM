import numpy as np
import pandas as pd

from tfm_airquality import config
from tfm_airquality.clean import clean
from tfm_airquality.features import (
    add_calendar,
    add_lags,
    add_rolling,
    build_features,
)
from tfm_airquality.load import load_airquality_data

def test_sin_fuga_de_informacion():
    """
    Ninguna variable de entrada puede depender de valores futuros.

    Se altera todo lo posterior a un instante y se comprueba que las variables
    construidas en ese instante no cambian.
    """
    df, _ = clean(load_airquality_data())
    t = 5000

    columnas_datos = [c for c in df.columns
                      if c in config.SENSOR_COLUMNS + config.MET_COLUMNS
                      or c == config.TARGET]

    original = build_features(df, horizontes=[24])

    alterado = df.copy()
    alterado.loc[alterado.index[t + 1:], columnas_datos] += 999
    modificado = build_features(alterado, horizontes=[24])

    # Se excluye 'y': es la respuesta a predecir, y sí depende del futuro.
    columnas = [c for c in original.columns if c != 'y']

    pd.testing.assert_series_equal(
        original[columnas].iloc[t],
        modificado[columnas].iloc[t],
    )

def test_lag_mira_al_pasado():
    """El retardo de 24 horas debe contener el valor de 24 horas antes."""
    idx = pd.date_range('2004-03-10', periods=50, freq='h', name='DateTime')
    df = pd.DataFrame({'T': np.arange(50, dtype=float)}, index=idx)

    d = add_lags(df, ['T'], lags=(24,))

    assert d['T_lag24'].iloc[:24].isna().all()
    assert d['T_lag24'].iloc[24] == df['T'].iloc[0]
    assert d['T_lag24'].iloc[30] == df['T'].iloc[6]


def test_hora_ciclica_es_continua():
    """
    Las 23:00 y las 00:00 deben quedar próximas en la codificación cíclica.

    Con la hora como entero, ambas están en extremos opuestos de la escala
    pese a ser consecutivas.
    """
    idx = pd.date_range('2004-03-10 00:00', periods=24, freq='h', name='DateTime')
    df = pd.DataFrame({'x': range(24)}, index=idx)
    d = add_calendar(df)

    def distancia(h1, h2):
        return np.hypot(d['hora_sin'].iloc[h1] - d['hora_sin'].iloc[h2],
                        d['hora_cos'].iloc[h1] - d['hora_cos'].iloc[h2])

    assert distancia(23, 0) < distancia(0, 12)


def test_objetivo_desplazado():
    """
    La columna y debe contener el valor del objetivo h horas después.

    Si el signo del desplazamiento estuviera invertido, el modelo predeciría
    el pasado y las métricas saldrían excelentes sin significar nada.
    """
    df, _ = clean(load_airquality_data())
    tabla = build_features(df, horizontes=[24])

    t = 1000
    esperado = df[config.TARGET].iloc[t + 24]
    obtenido = tabla['y'].iloc[t]

    assert obtenido == esperado or (pd.isna(obtenido) and pd.isna(esperado))