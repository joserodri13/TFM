import pandas as pd
from tfm_airquality.load import load_airquality_data
from tfm_airquality.validate import validate

def test_valid_data():
    """El dataset original debe superar el data contract."""
    df = load_airquality_data()
    resultado = validate(df)
    assert resultado.ok


def test_missing_column():
    """La ausencia de una columna esperada debe tumbar el data contract."""
    df = load_airquality_data()
    assert not validate(df.drop(columns=['T'])).ok


def test_impossible_humidity():
    """
    Un valor físicamente imposible debe tumbar el data contract.
    """
    df = load_airquality_data()
    malo = df.copy()
    malo.loc[malo.index[100], 'RH'] = 4820
    assert not validate(malo).ok


def test_missing_hours():
    """
    Un salto en la serie horaria debe tumbar el data contract.
    """
    df = load_airquality_data()
    assert not validate(df.drop(index=df.index[500:510])).ok


def test_informative_check_does_not_block():
    """
    Un aviso informativo no debe tumbar el data contract.

    Recortar filas del final altera el número de filas (informativo) sin
    romper la continuidad horaria (bloqueante).
    """
    df = load_airquality_data()
    informe = validate(df.iloc[:-100])

    assert informe.ok
    assert informe.avisos