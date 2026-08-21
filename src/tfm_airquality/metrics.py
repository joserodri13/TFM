import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error


def evaluate(y_true, y_pred):
    """
    MAE, RMSE y número de observaciones puntuadas.

    Descarta las posiciones sin valor real: no se puntúa contra un valor
    inventado. sklearn no admite NaN, así que hay que limpiar antes.
    """
    par = pd.concat([y_true.rename('real'), y_pred.rename('pred')], axis=1).dropna()

    if len(par) == 0:
        return {'MAE': np.nan, 'RMSE': np.nan, 'n': 0}

    return {
        'MAE': mean_absolute_error(par['real'], par['pred']),
        'RMSE': root_mean_squared_error(par['real'], par['pred']),
        'n': len(par),
    }


def skill_score(mae_modelo, mae_baseline):
    """Mejora relativa frente al baseline. 0 = igual, >0 = mejor, <0 = peor."""
    if mae_baseline in (0, None) or np.isnan(mae_baseline):
        return np.nan
    return 1 - mae_modelo / mae_baseline