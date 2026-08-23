import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from tfm_airquality import explain as ex
from tfm_airquality import model as md
from tfm_airquality.clean import clean
from tfm_airquality.features import build_features
from tfm_airquality.load import load_airquality_data
from tfm_airquality.split import split_temporal


def _modelo_entrenado():
    df, _ = clean(load_airquality_data())
    tabla = build_features(df, horizontes=[24])
    train, test = split_temporal(tabla)

    cols = md.feature_columns(train, 'A')
    tr = train[cols + ['y']].dropna()
    te = test[cols + ['y']].dropna().head(200)

    modelo = LGBMRegressor(n_estimators=50, random_state=42, verbose=-1)
    modelo.fit(tr[cols], tr['y'])
    return modelo, te[cols]


def test_shap_suma_la_prediccion():
    """
    Los valores SHAP más el valor base deben reconstruir la predicción.

    Es la propiedad que define el método: el reparto entre variables es
    exhaustivo. Si no se cumple, el cálculo está mal montado.
    """
    import shap

    modelo, X = _modelo_entrenado()
    explainer = shap.TreeExplainer(modelo)
    valores = explainer.shap_values(X.head(20))

    reconstruido = explainer.expected_value + valores.sum(axis=1)
    esperado = modelo.predict(X.head(20))

    assert np.allclose(reconstruido, esperado, atol=1e-4)


def test_importancia_global_ordenada_y_positiva():
    """La importancia es una media de valores absolutos: nunca negativa."""
    modelo, X = _modelo_entrenado()
    sv, _ = ex.shap_values(modelo, X, muestra=100)
    imp = ex.global_importance(sv)

    assert (imp >= 0).all()
    assert imp.is_monotonic_decreasing
    assert len(imp) == X.shape[1]