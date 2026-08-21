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
    gt = [c for c in config.GT_COLUMNS]
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
                                          max_iter=300, random_state=42)),
    }


def train_evaluate(tabla_train, tabla_test, escenario='A', modelos=None):
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