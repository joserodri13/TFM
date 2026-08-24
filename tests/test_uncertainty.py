import numpy as np
import pandas as pd

from tfm_airquality import uncertainty as unc


def test_ancho_crece_con_la_cobertura():
    """A mayor cobertura exigida, intervalo más ancho."""
    errores = np.abs(np.random.default_rng(42).normal(0, 30, 1000))

    w80 = unc.conformal_width(errores, cobertura=0.8)
    w90 = unc.conformal_width(errores, cobertura=0.9)
    w95 = unc.conformal_width(errores, cobertura=0.95)

    assert w80 < w90 < w95


def test_cobertura_se_cumple_si_los_datos_son_intercambiables():
    """
    Con datos de la misma distribución, la cobertura real debe alcanzar la
    nominal.

    Es la garantía que ofrece el método. Si no se cumple aquí, el cálculo del
    cuantil está mal; si no se cumple con datos reales, es que la
    intercambiabilidad no se sostiene.
    """
    rng = np.random.default_rng(42)

    # Calibracion y evaluacion de la misma distribucion
    err_cal = np.abs(rng.normal(0, 30, 2000))
    pred = np.full(2000, 100.0)
    real = pd.Series(100 + rng.normal(0, 30, 2000))

    w = unc.conformal_width(err_cal, cobertura=0.9)
    r = unc.evaluate_coverage(real, pred, w)

    assert r['cobertura'] >= 0.88


def test_probabilidad_crece_con_la_prediccion():
    """
    Una predicción más alta debe dar mayor probabilidad de superar el umbral.

    Los errores se pasan con signo, no en valor absoluto: la dirección
    determina si el error empuja por encima o por debajo del límite.
    """
    errores = np.random.default_rng(42).normal(0, 30, 1000)

    probs = unc.exceedance_probability([100, 150, 195, 250], errores, umbral=200)

    assert list(probs) == sorted(probs)
    assert probs[0] < 0.05      # 100 muy por debajo del umbral
    assert probs[-1] > 0.90     # 250 muy por encima