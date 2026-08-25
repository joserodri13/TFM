import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd

from tfm_airquality import config


def save_model(modelo, columnas, errores_calibracion, horizontes_calibracion,
               umbral_alerta=config.UMBRAL_ALERTA, nombre=config.MODEL_NAME):
    """
    Guarda el modelo junto con todo lo que necesita para funcionar.

    Un modelo sin sus metadatos es inservible: si las columnas llegan en otro
    orden, predice sin protestar y el resultado es basura.

    Se guardan también los errores de calibración y el horizonte al que
    corresponde cada uno, para poder construir intervalos por horizonte.
    """
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(modelo, config.MODELS_DIR / f'{nombre}.joblib')
    np.save(config.MODELS_DIR / f'{nombre}_errores.npy',
            np.asarray(errores_calibracion))
    np.save(config.MODELS_DIR / f'{nombre}_horizontes_cal.npy',
            np.asarray(horizontes_calibracion))

    metadatos = {
        'nombre': nombre,
        'creado': datetime.now(timezone.utc).isoformat(),
        'columnas': list(columnas),
        'n_columnas': len(columnas),
        'horizontes': list(config.HORIZONTES),
        'umbral_legal': config.UMBRAL_LEGAL,
        'umbral_alerta': umbral_alerta,
        'cobertura': config.COBERTURA,
        'n_calibracion': len(errores_calibracion),
    }

    with open(config.MODELS_DIR / f'{nombre}_meta.json', 'w',
              encoding='utf-8') as f:
        json.dump(metadatos, f, indent=2, ensure_ascii=False)

    return config.MODELS_DIR


def load_model(nombre=config.MODEL_NAME):
    """Carga el modelo, los errores de calibración con su horizonte y los metadatos."""
    modelo = joblib.load(config.MODELS_DIR / f'{nombre}.joblib')
    errores = np.load(config.MODELS_DIR / f'{nombre}_errores.npy')
    horizontes_cal = np.load(config.MODELS_DIR / f'{nombre}_horizontes_cal.npy')

    with open(config.MODELS_DIR / f'{nombre}_meta.json', encoding='utf-8') as f:
        meta = json.load(f)

    return modelo, errores, horizontes_cal, meta


def predict(entrada, nombre=config.MODEL_NAME):
    """
    Predicción completa: valor, intervalo y probabilidad de superación.

    El intervalo y la probabilidad se calculan con los errores del horizonte
    correspondiente a cada fila. Una anchura única para todos los horizontes
    ignoraría que a una hora vista el error es notablemente menor.
    """
    modelo, errores, horizontes_cal, meta = load_model(nombre)

    faltan = set(meta['columnas']) - set(entrada.columns)
    if faltan:
        raise ValueError(f'faltan columnas: {sorted(faltan)}')

    # Se reordenan según el orden de entrenamiento: pasarlas en otro orden
    # produciría predicciones erróneas sin lanzar ningún error.
    X = entrada[meta['columnas']]
    pred = modelo.predict(X)
    horizontes = X['horizonte'].to_numpy()

    cobertura = meta['cobertura']
    umbral_legal = meta['umbral_legal']

    inferiores, superiores, probs = [], [], []

    for p, h in zip(pred, horizontes):
        err_h = errores[horizontes_cal == h]
        if len(err_h) == 0:
            err_h = errores

        n = len(err_h)
        q = min(1.0, np.ceil((n + 1) * cobertura) / n)
        w = float(np.quantile(np.abs(err_h), q))

        # Una concentración no puede ser negativa.
        inferiores.append(max(p - w, 0.0))
        superiores.append(p + w)
        probs.append(float(np.mean(p + err_h > umbral_legal)))

    # Se redondea antes de comparar con el umbral: si no, una probabilidad de
    # 0,0996 se mostraría como 0,1 pero no dispararía la alerta.
    probs = np.round(probs, 3)

    return pd.DataFrame({
        'prediccion': np.round(pred, 1),
        'inferior': np.round(inferiores, 1),
        'superior': np.round(superiores, 1),
        'prob_superacion': probs,
        'alerta': probs >= meta['umbral_alerta'],
    }, index=entrada.index)