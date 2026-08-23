import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from tfm_airquality import config


def shap_values(modelo, X, muestra=2000, seed=42):
    """
    Calcula los valores SHAP de un modelo de árboles.

    muestra: número de filas sobre las que calcular. Con el conjunto completo
        el cálculo es lento y el resultado apenas cambia.
    """
    if len(X) > muestra:
        X = X.sample(muestra, random_state=seed)

    explainer = shap.TreeExplainer(modelo)
    valores = explainer.shap_values(X)

    return pd.DataFrame(valores, columns=X.columns, index=X.index), X


def global_importance(shap_df):
    """
    Importancia global: media del valor absoluto de cada variable.

    Se toma el valor absoluto porque una variable puede empujar la predicción
    hacia arriba en unos casos y hacia abajo en otros; lo que mide la
    importancia es cuánto mueve, no en qué dirección.
    """
    return shap_df.abs().mean().sort_values(ascending=False)

def plot_summary(shap_df, X, max_display=20, figsize=(9, 8)):
    """
    Resumen SHAP: importancia y dirección del efecto de cada variable.

    Cada punto es una predicción. La posición horizontal indica cuánto empujó
    esa variable la predicción; el color, si su valor era alto o bajo. Permite
    ver no solo qué variables importan, sino en qué sentido actúan.
    """
    fig = plt.figure(figsize=figsize)
    shap.summary_plot(shap_df.to_numpy(), X, max_display=max_display,
                      show=False)
    plt.tight_layout()
    return fig


def plot_importance_bar(imp, top=20, figsize=(8, 7)):
    """Importancia global: media del valor absoluto de cada variable."""
    datos = imp.head(top).iloc[::-1]

    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(datos.index, datos.values)
    ax.set_xlabel('|SHAP| medio (µg/m³)')
    ax.grid(alpha=0.3, axis='x')
    fig.tight_layout()
    return fig

def explain_prediction(modelo, X, indice, top=10):
    """
    Desglosa una predicción concreta en la aportación de cada variable.

    Devuelve la predicción, el valor base (media de las predicciones del
    modelo) y las variables que más han contribuido, con su valor y su
    aportación en µg/m³.
    """
    explainer = shap.TreeExplainer(modelo)
    fila = X.loc[[indice]] if not isinstance(indice, int) else X.iloc[[indice]]

    valores = explainer.shap_values(fila)[0]

    detalle = pd.DataFrame({
        'valor': fila.iloc[0],
        'aportacion': valores,
    })
    detalle = detalle.reindex(
        detalle['aportacion'].abs().sort_values(ascending=False).index
    )

    return {
        'base': explainer.expected_value,
        'prediccion': modelo.predict(fila)[0],
        'detalle': detalle.head(top).round(2),
    }