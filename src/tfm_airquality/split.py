import pandas as pd

from tfm_airquality import config


def split_temporal(df, corte=config.FECHA_CORTE, embargo_horas=48):
    """
    Parte la tabla en entrenamiento y test por una fecha, con embargo.

    En series temporales no se reparte al azar: todo lo de entrenamiento debe
    ser anterior a todo lo de evaluación, o el modelo aprende del futuro.

    El embargo descarta las últimas horas previas al corte. Sin él, la fila del
    31/12 a las 23:00 con horizonte 24 tendría su respuesta en el 1 de enero,
    es decir, dentro del periodo de evaluación.

    embargo_horas: debe igualar al horizonte máximo de predicción.
    """
    if not df.index.is_monotonic_increasing:
        df = df.sort_index()

    fin_train = corte - pd.Timedelta(hours=embargo_horas)

    train = df[df.index < fin_train]
    test = df[df.index >= corte]

    if len(train) == 0 or len(test) == 0:
        raise ValueError(
            f'El corte {corte:%d/%m/%Y} deja un tramo vacío. '
            f'Rango disponible: {df.index.min():%d/%m/%Y} a {df.index.max():%d/%m/%Y}.'
        )

    return train, test