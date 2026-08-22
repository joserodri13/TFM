import pandas as pd

from tfm_airquality import config
from tfm_airquality import model as md
from tfm_airquality.clean import clean
from tfm_airquality.features import build_features
from tfm_airquality.load import load_airquality_data
from tfm_airquality.split import split_temporal


def test_escenario_b_excluye_el_analizador():
    """
    El escenario B no puede usar ninguna variable derivada del analizador.

    Si se colara NO2(GT)_lag24, el escenario estaría empleando el equipo del
    que supuestamente no dispone, y su resultado carecería de sentido.
    """
    df, _ = clean(load_airquality_data())
    tabla = build_features(df, horizontes=[24])

    cols = md.feature_columns(tabla, 'B')

    for gt in config.GT_COLUMNS:
        assert not any(c == gt or c.startswith(f'{gt}_') for c in cols), \
            f'el escenario B incluye una variable derivada de {gt}'


def test_el_objetivo_no_esta_entre_las_entradas():
    """
    La columna y nunca puede ser una variable de entrada.

    Sería predecir la respuesta a partir de sí misma: el modelo daría un error
    prácticamente nulo y sin ningún valor.
    """
    df, _ = clean(load_airquality_data())
    tabla = build_features(df, horizontes=[24])

    for escenario in ['A', 'B']:
        assert 'y' not in md.feature_columns(tabla, escenario)


def test_train_evaluate_devuelve_una_fila_por_horizonte():
    """La evaluación debe cubrir todos los horizontes solicitados."""
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    df, _ = clean(load_airquality_data())
    tabla = build_features(df, horizontes=[1, 24])
    train, test = split_temporal(tabla)

    modelo = {'ridge': make_pipeline(StandardScaler(), Ridge())}
    r = md.train_evaluate(train, test, escenario='A', modelos=modelo)

    assert sorted(r['horizonte'].unique()) == [1, 24]
    assert (r['n'] > 0).all()