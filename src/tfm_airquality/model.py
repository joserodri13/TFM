import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from tfm_airquality import config, metrics
from sklearn.base import clone


# Escenario A: todas las variables disponibles, incluidos los retardos del
# objetivo y las demás mediciones del analizador. Es el techo de rendimiento.
# Escenario B: solo el nodo de sensores baratos.
def feature_columns(tabla, escenario):
    """Selecciona las columnas de entrada según el escenario de despliegue."""
    excluir = {'y'}
    columnas = [c for c in tabla.columns if c not in excluir]

    if escenario == 'A':
        return columnas

    # En el escenario B no se dispone de ninguna medición del analizador,
    # ni directa ni derivada.
    gt = config.GT_COLUMNS
    return [c for c in columnas
            if not any(c == g or c.startswith(f'{g}_') for g in gt)]


def build_models():
    """
    Los seis modelos de la escalera, con hiperparámetros por defecto.

    Ridge y MLP se envuelven en un pipeline con escalado: son sensibles a la
    escala de las variables, y aquí conviven señales de sensores en miles con
    variables cíclicas entre -1 y 1. Los modelos de árboles no lo necesitan.
    """
    return {
        'ridge': make_pipeline(StandardScaler(), Ridge()),
        'random_forest': RandomForestRegressor(n_estimators=100, n_jobs=-1,
                                               random_state=42),
        'lightgbm': LGBMRegressor(n_estimators=200, random_state=42, verbose=-1),
        'xgboost': XGBRegressor(n_estimators=200, random_state=42),
        'mlp': make_pipeline(StandardScaler(),
                             MLPRegressor(hidden_layer_sizes=(64, 32),
                                          max_iter=1000, early_stopping=True,
                                          n_iter_no_change=20, random_state=42)),
    }


def train_evaluate(tabla_train, tabla_test, escenario, modelos=None):
    """
    Entrena cada modelo y devuelve su MAE por horizonte sobre el test.

    Ambas tablas se restringen a filas completas para que la comparación entre
    modelos sea equitativa: Ridge, Random Forest y MLP no admiten ausentes.
    """
    modelos = modelos or build_models()
    cols = feature_columns(tabla_train, escenario)

    train = tabla_train[cols + ['y']].dropna()
    test = tabla_test[cols + ['y']].dropna()

    X_train, y_train = train[cols], train['y']
    X_test, y_test = test[cols], test['y']

    filas = []
    for nombre, modelo in modelos.items():
        modelo.fit(X_train, y_train)
        pred = pd.Series(modelo.predict(X_test), index=X_test.index)

        for h in sorted(test['horizonte'].unique()):
            mascara = X_test['horizonte'] == h
            r = metrics.evaluate(y_test[mascara], pred[mascara])
            filas.append({'modelo': nombre, 'horizonte': h, **r})

    return pd.DataFrame(filas)

from sklearn.model_selection import GridSearchCV, TimeSeriesSplit


# Rejillas deliberadamente pequeñas: el objetivo de esta fase es comprobar si
# hay margen de mejora, no exprimir el último decimal.
PARAM_GRIDS = {
    'random_forest': {
        'max_depth': [10, 20, None],
        'min_samples_leaf': [1, 5, 20],
    },
    'lightgbm': {
        'n_estimators': [500, 1000],
        'num_leaves': [63, 127],
        'learning_rate': [0.03, 0.05],
    },
    'xgboost': {
        'n_estimators': [200, 500],
        'max_depth': [4, 8],
        'learning_rate': [0.05, 0.1],
    },
}


def tune(tabla_train, nombre, escenario, n_splits=3):
    """
    Busca hiperparámetros con validación cruzada temporal.

    Se emplea TimeSeriesSplit y no la validación cruzada por defecto: un
    reparto aleatorio permitiría entrenar con datos posteriores a los de
    validación, lo que produciría métricas excelentes y sin validez.

    La tabla se ordena por fecha antes de partir, porque contiene cada
    instante repetido una vez por horizonte y las particiones se hacen por
    posición de fila.
    """
    cols = feature_columns(tabla_train, escenario)
    datos = tabla_train[cols + ['y']].dropna().sort_index()

    busqueda = GridSearchCV(
        estimator=build_models()[nombre],
        param_grid=PARAM_GRIDS[nombre],
        cv=TimeSeriesSplit(n_splits=n_splits),
        scoring='neg_mean_absolute_error',
        n_jobs=-1,
        verbose=1,
    )
    busqueda.fit(datos[cols], datos['y'])

    return busqueda

def train_by_range(tabla_train, tabla_test, escenario, corte=12, modelo=None):
    """
    Entrena un modelo por tramo de horizonte, frente a uno único global.

    La hipótesis es que corto y largo plazo se benefician de configuraciones
    distintas. El coste es mantener dos modelos en producción en lugar de uno.
    """

    modelo = modelo or build_models()['lightgbm']
    cols = feature_columns(tabla_train, escenario)

    filas = []
    for etiqueta, filtro in [
        ('corto', lambda h: h <= corte),
        ('largo', lambda h: h > corte),
    ]:
        tr = tabla_train[tabla_train['horizonte'].apply(filtro)]
        te = tabla_test[tabla_test['horizonte'].apply(filtro)]

        tr = tr[cols + ['y']].dropna()
        te = te[cols + ['y']].dropna()

        m = clone(modelo)
        m.fit(tr[cols], tr['y'])
        pred = pd.Series(m.predict(te[cols]), index=te.index)

        for h in sorted(te['horizonte'].unique()):
            mascara = te['horizonte'] == h
            r = metrics.evaluate(te['y'][mascara], pred[mascara])
            filas.append({'tramo': etiqueta, 'horizonte': h, **r})

    return pd.DataFrame(filas)

def train_by_bins(tabla_train, tabla_test, escenario, bins, modelo=None):
    """
    Entrena un modelo por cada tramo de horizontes.

    bins: lista de tuplas (h_min, h_max), ambos inclusive.
    """
    modelo = modelo or build_models()['lightgbm']
    cols = feature_columns(tabla_train, escenario)

    filas = []
    for h_min, h_max in bins:
        en_tramo = lambda t: (t['horizonte'] >= h_min) & (t['horizonte'] <= h_max)

        tr = tabla_train[en_tramo(tabla_train)][cols + ['y']].dropna()
        te = tabla_test[en_tramo(tabla_test)][cols + ['y']].dropna()

        m = clone(modelo)
        m.fit(tr[cols], tr['y'])
        pred = pd.Series(m.predict(te[cols]), index=te.index)

        for h in sorted(te['horizonte'].unique()):
            mascara = te['horizonte'] == h
            r = metrics.evaluate(te['y'][mascara], pred[mascara])
            filas.append({'tramo': f'{h_min}-{h_max}', 'horizonte': h, **r})

    return pd.DataFrame(filas)