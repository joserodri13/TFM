import matplotlib.pyplot as plt
import pandas as pd

from tfm_airquality import config


def correlacion_por_horizonte(df, variables=None, horizontes=(0, 1, 6, 24, 48)):
    """
    Correlación de cada variable con el objetivo desplazado a cada horizonte.

    La correlación contemporánea no mide capacidad predictiva: lo relevante es
    la relación entre el valor de ahora y el objetivo de dentro de h horas.
    """
    if variables is None:
        variables = [c for c in df.columns
                     if c in config.SENSOR_COLUMNS + config.MET_COLUMNS
                     or c in config.GT_COLUMNS]
        variables = [c for c in variables if c != config.TARGET]

    y = df[config.TARGET]

    filas = []
    for col in variables:
        fila = {'variable': col}
        for h in horizontes:
            fila[f'h+{h}' if h else 'lag0'] = df[col].corr(y.shift(-h))
        filas.append(fila)

    return pd.DataFrame(filas).set_index('variable').round(3)