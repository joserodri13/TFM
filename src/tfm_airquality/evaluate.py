import pandas as pd

from tfm_airquality import config, metrics
from tfm_airquality.baselines import BASELINES, persistence


def future_values(serie, horizonte):
    """
    El valor real a acertar: NO2(t+h), indexado en t.

    Único shift negativo legítimo: es la respuesta, no una entrada. Las
    últimas h filas quedan sin valor porque su futuro se sale del histórico.
    """
    return serie.shift(-horizonte)


def evaluate_method(metodo, serie_completa, indice_test, horizontes=config.HORIZONTES):
    """
    Aplica un método a todos los horizontes y puntúa sobre el periodo de test.

    Recibe la serie COMPLETA, no solo el test: para predecir las primeras
    horas de enero, un baseline necesita mirar diciembre. El recorte al test
    se hace al final, cuando ya están calculados predicción y valor real.
    """
    idx = serie_completa.index.intersection(indice_test)
    filas = []

    for h in horizontes:
        real = future_values(serie_completa, h).loc[idx]
        pred = metodo(serie_completa, h).loc[idx]

        resultado = metrics.evaluate(real, pred)
        resultado['horizonte'] = h
        filas.append(resultado)

    return pd.DataFrame(filas).set_index('horizonte')


def evaluate_baselines(serie_completa, indice_test, horizontes=config.HORIZONTES):
    """
    Evalúa los tres baselines y añade el skill score frente a la persistencia.

    Devuelve un diccionario {nombre: tabla de métricas por horizonte}.
    """
    tabla_persistencia = evaluate_method(persistence, serie_completa,
                                         indice_test, horizontes)
    referencia = tabla_persistencia['MAE']

    resultados = {}
    for nombre, funcion in BASELINES.items():
        tabla = evaluate_method(funcion, serie_completa, indice_test, horizontes)
        tabla['skill'] = [
            metrics.skill_score(m, referencia[h]) for h, m in tabla['MAE'].items()
        ]
        resultados[nombre] = tabla

    return resultados

def best_baseline(resultados):
    """
    Mejor baseline en cada horizonte, con su MAE.

    Es el listón que el modelo debe superar en la estación 7. Se exige batir
    al MEJOR de los baselines, no a uno cualquiera: ganarle al más flojo no
    demostraría nada.
    """
    tablas = {nombre: t['MAE'] for nombre, t in resultados.items()}
    maes = pd.DataFrame(tablas)

    return pd.DataFrame({
        'mejor_baseline': maes.idxmin(axis=1),
        'MAE': maes.min(axis=1),
    })