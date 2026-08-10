import numpy as np
import pandas as pd

from tfm_airquality import config
from tfm_airquality.clean import (
    clean,
    gap_runs,
    interpolate_short_gaps,
    sentinel_to_nan,
)
from tfm_airquality.load import load_airquality_data


def serie_sintetica(n=50):
    """Serie horaria sin huecos, para probar reglas de forma aislada."""
    idx = pd.date_range('2004-03-10 00:00', periods=n, freq='h', name='DateTime')
    return pd.Series(np.arange(n, dtype=float) * 10, index=idx)


def test_sentinel_to_nan():
    """El marcador -200 debe desaparecer y convertirse en hueco."""
    df = load_airquality_data()
    limpio = sentinel_to_nan(df)
    assert (limpio == config.MISSING_SENTINEL).sum().sum() == 0
    assert limpio.isna().sum().sum() == (df == config.MISSING_SENTINEL).sum().sum()


def test_gap_runs_mide_longitudes():
    """gap_runs debe medir correctamente la longitud de cada racha."""
    s = serie_sintetica()
    s.iloc[5] = np.nan            # racha de 1 hora
    s.iloc[20:25] = np.nan        # racha de 5 horas
    rachas = gap_runs(s)
    assert len(rachas) == 2
    assert sorted(rachas['horas']) == [1, 5]


def test_hueco_corto_se_interpola():
    """Un hueco de una hora debe rellenarse con la media de sus vecinos."""
    s = serie_sintetica()
    s.iloc[10] = np.nan
    salida, marcas = interpolate_short_gaps(s.to_frame('T'), ['T'], max_horas=2)
    assert salida['T'].iloc[10] == (s.iloc[9] + s.iloc[11]) / 2
    assert marcas['T'].iloc[10]


def test_hueco_largo_queda_intacto():
    """
    Una racha larga debe quedar sin tocar de principio a fin.

    df.interpolate(limit=2) rellenaría las dos primeras horas de un hueco de
    diez, inventando datos al principio de una parada del equipo.
    """
    s = serie_sintetica()
    s.iloc[20:30] = np.nan        # racha de 10 horas
    salida, marcas = interpolate_short_gaps(s.to_frame('T'), ['T'], max_horas=2)
    assert salida['T'].iloc[20:30].isna().all()
    assert not marcas['T'].iloc[20:30].any()


def test_el_objetivo_nunca_se_interpola():
    """Los huecos de la variable objetivo deben conservarse."""
    limpio, _ = clean(load_airquality_data())
    rachas = gap_runs(limpio[config.TARGET])
    assert (rachas['horas'] == 1).sum() > 0


def test_clean_completo():
    """La tabla limpia conserva todas las filas, descarta NMHC y deja 7.396 horas útiles."""
    df = load_airquality_data()
    limpio, _ = clean(df)

    assert limpio.index.equals(df.index)
    assert 'NMHC(GT)' not in limpio.columns
    assert 'C6H6(GT)' not in limpio.columns

    utiles = limpio['objetivo_observado'] & limpio['entradas_completas']
    assert utiles.sum() == 7396