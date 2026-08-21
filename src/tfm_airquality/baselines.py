import pandas as pd


def persistence(serie, horizonte):
    """NO2(t+h) ≈ NO2(t). El último valor conocido."""
    return serie.copy()


def daily_seasonal(serie, horizonte):
    """
    NO2(t+h) ≈ valor de la misma hora del día anterior.

    Para horizontes de más de 24 horas se retrocede dos días en lugar de uno:
    con un solo día, t+h-24 caería en el futuro.
    """
    k = 24 if horizonte <= 24 else 48
    return serie.shift(k - horizonte)


def weekly_seasonal(serie, horizonte):
    """NO2(t+h) ≈ valor de la misma hora del mismo día de la semana anterior."""
    return serie.shift(168 - horizonte)


BASELINES = {
    'persistence': persistence,
    'daily_seasonal': daily_seasonal,
    'weekly_seasonal': weekly_seasonal,
}