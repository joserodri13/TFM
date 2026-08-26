import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from tfm_airquality import config

# Umbrales convencionales del PSI, procedentes de su uso habitual en modelos
# de riesgo. Se emplea PSI y no un contraste de hipótesis porque, con miles de
# observaciones, un test como el de Kolmogorov-Smirnov detecta diferencias
# estadísticamente significativas pero irrelevantes en la práctica.
PSI_ESTABLE = 0.10
PSI_MODERADO = 0.25


def psi(referencia, actual, n_bins=10):
    """
    Population Stability Index entre dos distribuciones.

    Reparte la referencia en n_bins de igual frecuencia y compara qué
    proporción de cada muestra cae en cada uno. Cuanto mayor el índice, más se
    ha desplazado la distribución.
    """
    referencia = pd.Series(referencia).dropna()
    actual = pd.Series(actual).dropna()

    if len(referencia) == 0 or len(actual) == 0:
        return np.nan

    # Cortes por cuantiles de la referencia
    cortes = np.unique(np.quantile(referencia, np.linspace(0, 1, n_bins + 1)))
    cortes[0], cortes[-1] = -np.inf, np.inf

    p_ref = np.histogram(referencia, bins=cortes)[0] / len(referencia)
    p_act = np.histogram(actual, bins=cortes)[0] / len(actual)

    # Se sustituyen los ceros por un valor mínimo: el logaritmo de cero no
    # está definido.
    eps = 1e-6
    p_ref = np.clip(p_ref, eps, None)
    p_act = np.clip(p_act, eps, None)

    return float(np.sum((p_act - p_ref) * np.log(p_act / p_ref)))


def drift_report(referencia, actual, columnas=None):
    """Informe de deriva por variable, con PSI y test de Kolmogorov-Smirnov."""
    columnas = columnas or [c for c in config.MONITOR_COLUMNS
                            if c in referencia.columns]

    filas = []
    for col in columnas:
        valor = psi(referencia[col], actual[col])

        if valor < PSI_ESTABLE:
            estado = 'estable'
        elif valor < PSI_MODERADO:
            estado = 'moderado'
        else:
            estado = 'significativo'

        ks = ks_2samp(referencia[col].dropna(), actual[col].dropna())

        filas.append({
            'variable': col,
            'PSI': round(valor, 4),
            'estado': estado,
            'KS_pvalor': round(float(ks.pvalue), 6),
            'media_ref': round(float(referencia[col].mean()), 1),
            'media_act': round(float(actual[col].mean()), 1),
        })

    return pd.DataFrame(filas).sort_values('PSI', ascending=False)

def performance_report(y_real, y_pred, inferior, superior, ventana='ME'):
    """
    Evolución del error y de la cobertura por periodos.

    A diferencia de la deriva de entrada, esta comprobación solo puede
    realizarse cuando llega la medición real, es decir, con el retardo del
    horizonte de predicción.
    """
    datos = pd.DataFrame({
        'real': y_real, 'pred': y_pred,
        'inferior': inferior, 'superior': superior,
    }).dropna()

    datos['error'] = (datos['real'] - datos['pred']).abs()
    datos['dentro'] = ((datos['real'] >= datos['inferior']) &
                       (datos['real'] <= datos['superior']))

    resumen = datos.resample(ventana).agg(
        MAE=('error', 'mean'),
        cobertura=('dentro', 'mean'),
        n=('error', 'size'),
    ).round(3)

    return resumen[resumen['n'] > 0]

def check_alerts(informe_deriva, informe_rendimiento, mae_referencia):
    """
    Aplica la política de actuación a los informes de monitorización.

    Distingue dos fenómenos que exigen respuestas distintas: la deriva del
    sensor, que es progresiva y no se recupera, y el cambio de régimen, que
    produce un pico de error transitorio.
    """
    avisos = []

    # 1. Deriva de entrada: se detecta de inmediato, sin esperar al valor real
    graves = informe_deriva[informe_deriva['PSI'] >= config.PSI_MODERADO]
    for _, f in graves.iterrows():
        avisos.append({
            'tipo': 'deriva_entrada',
            'variable': f['variable'],
            'valor': f['PSI'],
            'gravedad': 'alta' if f['PSI'] >= 1.0 else 'media',
            'accion': 'Verificar el sensor y recalibrar el modelo',
        })

    # 2. Cobertura por debajo de lo prometido
    baja = informe_rendimiento[
        informe_rendimiento['cobertura'] < config.COBERTURA_MINIMA
    ]
    for periodo, f in baja.iterrows():
        avisos.append({
            'tipo': 'cobertura_insuficiente',
            'variable': str(periodo.date()),
            'valor': f['cobertura'],
            'gravedad': 'alta' if f['cobertura'] < 0.80 else 'media',
            'accion': 'Recalibrar los intervalos con datos recientes',
        })

    # 3. Error muy por encima del de calibracion
    degradado = informe_rendimiento[
        informe_rendimiento['MAE'] > mae_referencia * config.DEGRADACION_MAE
    ]
    for periodo, f in degradado.iterrows():
        avisos.append({
            'tipo': 'error_elevado',
            'variable': str(periodo.date()),
            'valor': f['MAE'],
            'gravedad': 'alta',
            'accion': 'Reentrenar incorporando datos del periodo reciente',
        })

    return pd.DataFrame(avisos)