import numpy as np
import pandas as pd

from tfm_airquality import evaluate as ev
from tfm_airquality import metrics
from tfm_airquality.baselines import BASELINES
from tfm_airquality.clean import clean
from tfm_airquality.load import load_airquality_data
from tfm_airquality.split import split_temporal


def serie_sintetica(n=400):
    """Serie horaria con ciclo diario, para probar reglas de forma aislada."""
    idx = pd.date_range('2004-03-10 00:00', periods=n, freq='h', name='DateTime')
    hora = idx.hour.to_numpy()
    return pd.Series(100 + 30 * np.sin(2 * np.pi * hora / 24), index=idx)


def test_particion_con_embargo():
    """
    El entrenamiento debe terminar al menos 48 horas antes del test.

    Sin embargo, la última fila de entrenamiento tendría su valor objetivo
    dentro del periodo de evaluación.
    """
    df, _ = clean(load_airquality_data())
    train, test = split_temporal(df, embargo_horas=48)

    hueco = (test.index.min() - train.index.max()).total_seconds() / 3600
    assert hueco >= 48


def test_future_values_coge_el_valor_correcto():
    """El valor a acertar en t debe ser el de t+h."""
    s = serie_sintetica()
    real = ev.future_values(s, 24)

    assert real.iloc[100] == s.iloc[124]
    assert real.tail(24).isna().all()


def test_baselines_no_miran_al_futuro():
    """
    Ningún baseline puede depender de valores posteriores al instante actual.

    Se destroza todo el futuro de la serie y se comprueba que la predicción en
    ese instante no cambia.
    """
    s = serie_sintetica()
    t = 200

    for nombre, funcion in BASELINES.items():
        for h in [1, 24, 48]:
            antes = funcion(s, h).iloc[t]

            alterada = s.copy()
            alterada.iloc[t + 1:] += 999
            despues = funcion(alterada, h).iloc[t]

            iguales = antes == despues or (pd.isna(antes) and pd.isna(despues))
            assert iguales, f'{nombre} con h={h} mira al futuro'


def test_metricas_ignoran_ausentes():
    """Las posiciones sin valor real no se puntúan ni se rellenan."""
    idx = pd.date_range('2004-01-01', periods=5, freq='h')
    real = pd.Series([10.0, np.nan, 30.0, 40.0, np.nan], index=idx)
    pred = pd.Series([12.0, 20.0, 33.0, 44.0, 50.0], index=idx)

    r = metrics.evaluate(real, pred)
    assert r['n'] == 3
    assert abs(r['MAE'] - 3.0) < 1e-9