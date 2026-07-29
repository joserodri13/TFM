import pandas as pd
from tfm_airquality import config

def load_airquality_data(csv_path=config.PATH_CSV):
    """
    Carga el fichero de origen del dataset Air Quality (UCI).

    Lee el CSV en formato europeo, elimina las dos columnas 
    vacías y las filas finales sin fecha y construye el índice
    temporal a partir de Date y Time.

    Args:
        csv_path (Path | str): ruta al CSV de origen.

    Returns:
        pd.DataFrame: tabla indexada por DatetimeIndex horario, ordenada.
    """
    # Cargamos el dataset
    df = pd.read_csv(csv_path, delimiter=';', decimal=',')

    # Eliminar columnas vacias y filas sin datos en las columnas Date y Time
    df = df.dropna(axis=1, how='all')
    df = df.dropna(axis=0, subset=['Date', 'Time'])

    # Union de Date y Time en una sola columna de fecha (DateTime)
    # Asignar esa columna como índice y ordenar por fecha
    df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%d/%m/%Y %H.%M.%S')
    df = df.drop(['Date', 'Time'], axis=1)
    df = df.set_index('DateTime')
    df = df.sort_index()

    return df
