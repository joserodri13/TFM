import numpy as np
import pandas as pd

from tfm_airquality import config
from tfm_airquality import monitor as mon


def test_psi_es_cero_si_no_hay_cambio():
    """Comparar una distribución consigo misma no debe indicar deriva."""
    rng = np.random.default_rng(42)
    x = rng.normal(1000, 200, 5000)

    assert mon.psi(x, x) < 0.01


def test_psi_detecta_un_desplazamiento():
    """
    Un desplazamiento real debe superar el umbral de deriva significativa.

    Es lo que ocurre con PT08.S4, cuyo PSI pasa de 0,07 a 9,35 a lo largo del
    periodo.
    """
    rng = np.random.default_rng(42)
    referencia = rng.normal(1000, 200, 5000)
    desplazada = rng.normal(1500, 200, 5000)

    assert mon.psi(referencia, desplazada) > config.PSI_MODERADO


def test_psi_no_depende_del_tamano_de_muestra():
    """
    A diferencia de un contraste de hipótesis, el PSI no crece con el número
    de observaciones. Es el motivo de haberlo elegido: sobre los datos reales,
    el test de Kolmogorov-Smirnov devuelve un p-valor de cero incluso para
    variables sin deriva.
    """
    rng = np.random.default_rng(42)

    pequeno = mon.psi(rng.normal(0, 1, 500), rng.normal(0, 1, 500))
    grande = mon.psi(rng.normal(0, 1, 50000), rng.normal(0, 1, 50000))

    assert pequeno < config.PSI_ESTABLE
    assert grande < config.PSI_ESTABLE


def test_performance_report_calcula_la_cobertura():
    """La cobertura debe ser la proporción de valores dentro del intervalo."""
    idx = pd.date_range('2005-01-01', periods=100, freq='h')

    real = pd.Series(np.full(100, 100.0), index=idx)
    pred = pd.Series(np.full(100, 100.0), index=idx)
    inferior = pd.Series(np.full(100, 90.0), index=idx)
    superior = pd.Series(np.full(100, 110.0), index=idx)

    # Se sacan diez valores fuera del intervalo
    real.iloc[:10] = 200.0

    r = mon.performance_report(real, pred, inferior, superior)
    assert abs(r['cobertura'].iloc[0] - 0.9) < 0.01