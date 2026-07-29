import pandas as pd
from tfm_airquality.load import load_airquality_data


def test_shape():
    """La tabla debe tener 9.357 filas y 13 columnas."""
    df = load_airquality_data()
    assert df.shape == (9357, 13)


def test_index_is_datetime():
    """El índice debe ser temporal."""
    df = load_airquality_data()
    assert isinstance(df.index, pd.DatetimeIndex)


def test_index_is_sorted_and_unique():
    """El índice debe estar ordenado y sin duplicados: los retardos dependen de ello."""
    df = load_airquality_data()
    assert df.index.is_monotonic_increasing
    assert not df.index.has_duplicates


def test_date_time_columns_removed():
    """Date y Time deben haber pasado al índice."""
    df = load_airquality_data()
    assert 'Date' not in df.columns
    assert 'Time' not in df.columns
