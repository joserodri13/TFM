import numpy as np
import pandas as pd

from tfm_airquality import config


def split_calibration(train, fecha_corte=pd.Timestamp('2004-11-01')):
    """
    Parte el entrenamiento en ajuste y calibración, respetando el orden.

    El conjunto de calibración debe ser dato que el modelo no haya visto: sus
    errores sobre el entrenamiento son artificialmente bajos y producirían
    intervalos demasiado estrechos.
    """
    ajuste = train[train.index < fecha_corte]
    calibracion = train[train.index >= fecha_corte]
    return ajuste, calibracion


def conformal_width(errores_calibracion, cobertura=0.9):
    """
    Semianchura del intervalo con la cobertura solicitada.

    Es el cuantil correspondiente de los errores absolutos observados en
    calibración. No asume ninguna distribución concreta del error.
    """
    n = len(errores_calibracion)
    # Corrección de muestra finita: garantiza la cobertura para n finito.
    q = min(1.0, np.ceil((n + 1) * cobertura) / n)
    return float(np.quantile(errores_calibracion, q))

def evaluate_coverage(y_real, y_pred, semianchura):
    """
    Mide qué proporción de valores reales cae dentro del intervalo.

    Es la comprobación que valida la garantía: si la cobertura observada queda
    por debajo de la nominal, los datos de calibración no eran representativos
    del periodo evaluado.
    """
    dentro = (y_real >= y_pred - semianchura) & (y_real <= y_pred + semianchura)
    return {
        'cobertura': float(dentro.mean()),
        'anchura': 2 * semianchura,
        'n': int(len(y_real)),
    }

def exceedance_probability(y_pred, errores_calibracion, umbral=200.0):
    """
    Probabilidad de superar el umbral, estimada de forma empírica.

    Para cada predicción se cuenta qué proporción de los errores observados en
    calibración la situarían por encima del umbral. No asume ninguna
    distribución del error: usa la observada.
    """
    errores = np.asarray(errores_calibracion)
    y_pred = np.asarray(y_pred)

    # Errores con signo respecto a la prediccion: cuantos la llevarian
    # por encima del umbral.
    return np.array([
        float(np.mean(p + errores > umbral)) for p in y_pred
    ])

def conformal_width_by_horizon(errores, horizontes, cobertura=config.COBERTURA):
    """
    Semianchura del intervalo, calculada por separado para cada horizonte.

    Un intervalo único para todos los horizontes ignora que la incertidumbre
    crece al alejar la predicción: el MAE pasa de 17,7 a 1 hora hasta 31,3 a
    48 horas.
    """
    df = pd.DataFrame({'error': np.abs(errores), 'horizonte': horizontes})

    anchuras = {}
    for h, grupo in df.groupby('horizonte'):
        n = len(grupo)
        q = min(1.0, np.ceil((n + 1) * cobertura) / n)
        anchuras[int(h)] = float(np.quantile(grupo['error'], q))

    return anchuras

def exceedance_probability_by_horizon(y_pred, horizontes_pred,
                                      errores, horizontes_cal,
                                      umbral=config.UMBRAL_LEGAL):
    """Probabilidad de superación, usando los errores del horizonte correspondiente."""
    errores = np.asarray(errores)
    horizontes_cal = np.asarray(horizontes_cal)

    probs = []
    for p, h in zip(np.asarray(y_pred), np.asarray(horizontes_pred)):
        err_h = errores[horizontes_cal == h]
        if len(err_h) == 0:
            err_h = errores
        probs.append(float(np.mean(p + err_h > umbral)))

    return np.array(probs)