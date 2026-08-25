import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from tfm_airquality import serve

app = FastAPI(
    title='Predicción de NO₂',
    description='Predicción de NO₂ a 1-48 horas con intervalo de confianza y '
                'probabilidad de superación del límite legal.',
    version='1.0',
)


class Medicion(BaseModel):
    """Una observación de entrada con las variables que el modelo espera."""
    variables: dict[str, float] = Field(
        ..., description='Nombre de cada variable y su valor'
    )


@app.get('/health')
def health():
    """Comprueba que el servicio está vivo y el modelo se carga."""
    try:
        _, _, meta = serve.load_model()
        return {
            'estado': 'ok',
            'modelo': meta['nombre'],
            'creado': meta['creado'],
            'columnas': meta['n_columnas'],
            'horizontes': meta['horizontes'],
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f'modelo no disponible: {e}')


@app.post('/predict')
def predict(medicion: Medicion):
    """Devuelve predicción, intervalo y probabilidad de superación."""
    try:
        entrada = pd.DataFrame([medicion.variables])
        resultado = serve.predict(entrada)
        return resultado.iloc[0].to_dict()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))