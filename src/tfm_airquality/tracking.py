import mlflow
import mlflow.lightgbm

from tfm_airquality import config


def setup():
    """Configura el almacenamiento local y el experimento del proyecto."""
    config.MLFLOW_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(f'sqlite:///{config.MLFLOW_DB.as_posix()}')
    mlflow.set_experiment(config.MLFLOW_EXPERIMENT)


def log_model_run(nombre, modelo, params, metricas, tags=None):
    """
    Registra un entrenamiento completo: parámetros, métricas y modelo.

    Sin esto, la comparación entre modelos vive únicamente en la salida de
    consola y se pierde al cerrar la sesión.
    """
    with mlflow.start_run(run_name=nombre):
        mlflow.log_params(params)
        mlflow.log_metrics(metricas)

        if tags:
            mlflow.set_tags(tags)

        # MLflow serializa los modelos de sklearn con skops, que solo admite
        # tipos de su lista blanca. LightGBM y XGBoost tienen su propio
        # guardador; el resto pasa por el de sklearn.
        try:
            if 'LGBM' in type(modelo).__name__:
                mlflow.lightgbm.log_model(modelo, name='modelo')
            elif 'XGB' in type(modelo).__name__:
                mlflow.xgboost.log_model(modelo, name='modelo')
            else:
                mlflow.sklearn.log_model(modelo, name='modelo')
        except Exception as e:
            # El registro de metricas es lo esencial; si el modelo no puede
            # serializarse, se deja constancia y se continua.
            mlflow.set_tag('modelo_no_guardado', str(e)[:200])

        return mlflow.active_run().info.run_id