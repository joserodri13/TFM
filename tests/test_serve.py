import numpy as np
import pandas as pd
import pytest
from lightgbm import LGBMRegressor

from tfm_airquality import config
from tfm_airquality import model as md
from tfm_airquality import serve
from tfm_airquality.clean import clean
from tfm_airquality.features import build_features
from tfm_airquality.load import load_airquality_data
from tfm_airquality.split import split_temporal


def _datos():
    df, _ = clean(load_airquality_data())
    tabla = build_features(df, horizontes=[1, 24])
    train, test = split_temporal(tabla)
    cols = md.feature_columns(train, 'A')
    return train[cols + ['y']].dropna(), test[cols + ['y']].dropna(), cols


def test_guardar_y_cargar_no_altera_el_modelo():
    """
    El modelo recuperado debe predecir exactamente igual que el original.

    Un modelo corrupto al serializar no daría error: devolvería predicciones
    distintas sin avisar.
    """
    tr, te, cols = _datos()

    modelo = LGBMRegressor(n_estimators=50, random_state=42, verbose=-1)
    modelo.fit(tr[cols], tr['y'])

    serve.save_model(modelo, cols, np.zeros(10), np.full(10, 24),
                     nombre='test_tmp')
    cargado, _, _, meta = serve.load_model('test_tmp')

    assert np.allclose(modelo.predict(te[cols].head(30)),
                       cargado.predict(te[cols].head(30)))
    assert meta['columnas'] == list(cols)


def test_predict_rechaza_entrada_incompleta():
    """Faltar una columna debe producir un error explícito, no una predicción."""
    _, te, cols = _datos()

    with pytest.raises(ValueError, match='faltan columnas'):
        serve.predict(te[cols].drop(columns=['T']).head(5))


def test_predict_es_invariante_al_orden_de_las_columnas():
    """
    Pasar las columnas en otro orden no debe cambiar la predicción.

    Sin la reordenación interna, el modelo asignaría cada valor a la variable
    equivocada y predeciría sin lanzar ningún error.
    """
    _, te, cols = _datos()

    normal = serve.predict(te[cols].head(20))
    desordenado = serve.predict(te[cols[::-1]].head(20))

    assert np.allclose(normal['prediccion'], desordenado['prediccion'])


def test_intervalo_contiene_la_prediccion_y_no_es_negativo():
    """El intervalo debe rodear a la predicción y no bajar de cero."""
    _, te, cols = _datos()
    r = serve.predict(te[cols].head(200))

    assert (r['inferior'] <= r['prediccion']).all()
    assert (r['prediccion'] <= r['superior']).all()
    assert (r['inferior'] >= 0).all()


def test_la_alerta_respeta_el_umbral():
    """Se alerta si y solo si la probabilidad alcanza el umbral configurado."""
    _, te, cols = _datos()
    r = serve.predict(te[cols].head(200))

    esperado = r['prob_superacion'] >= config.UMBRAL_ALERTA
    assert (r['alerta'] == esperado).all()