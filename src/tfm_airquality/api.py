import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import RedirectResponse

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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "variables": {
                        "CO(GT)": 4.8,
                        "PT08.S1(CO)": 1581.0,
                        "PT08.S2(NMHC)": 1319.0,
                        "NOx(GT)": 281.0,
                        "PT08.S3(NOx)": 799.0,
                        "NO2(GT)": 151.0,
                        "PT08.S4(NO2)": 2083.0,
                        "PT08.S5(O3)": 1409.0,
                        "T": 10.3,
                        "RH": 64.2,
                        "AH": 0.8065,
                        "PT08.S1(CO)_lag1": 1383.0,
                        "PT08.S1(CO)_lag24": 1360.0,
                        "PT08.S2(NMHC)_lag1": 1020.0,
                        "PT08.S2(NMHC)_lag24": 1046.0,
                        "PT08.S3(NOx)_lag1": 1008.0,
                        "PT08.S3(NOx)_lag24": 1056.0,
                        "PT08.S4(NO2)_lag1": 1719.0,
                        "PT08.S4(NO2)_lag24": 1692.0,
                        "PT08.S5(O3)_lag1": 1104.0,
                        "PT08.S5(O3)_lag24": 1268.0,
                        "T_lag1": 9.8,
                        "T_lag24": 13.6,
                        "RH_lag1": 67.6,
                        "RH_lag24": 48.9,
                        "AH_lag1": 0.8185,
                        "AH_lag24": 0.7578,
                        "NO2(GT)_lag1": 135.0,
                        "NO2(GT)_lag24": 113.0,
                        "PT08.S1(CO)_roll3_mean": 1418.6667,
                        "PT08.S1(CO)_roll3_std": 147.7645,
                        "PT08.S1(CO)_roll24_mean": 1241.3333,
                        "PT08.S1(CO)_roll24_std": 140.4922,
                        "PT08.S2(NMHC)_roll3_mean": 1083.6667,
                        "PT08.S2(NMHC)_roll3_std": 210.8372,
                        "PT08.S2(NMHC)_roll24_mean": 813.7083,
                        "PT08.S2(NMHC)_roll24_std": 194.3499,
                        "PT08.S3(NOx)_roll3_mean": 970.0,
                        "PT08.S3(NOx)_roll3_std": 155.5217,
                        "PT08.S3(NOx)_roll24_mean": 1304.5833,
                        "PT08.S3(NOx)_roll24_std": 286.6385,
                        "PT08.S4(NO2)_roll3_mean": 1797.6667,
                        "PT08.S4(NO2)_roll3_std": 255.2593,
                        "PT08.S4(NO2)_roll24_mean": 1471.375,
                        "PT08.S4(NO2)_roll24_std": 207.3925,
                        "PT08.S5(O3)_roll3_mean": 1156.6667,
                        "PT08.S5(O3)_roll3_std": 230.5566,
                        "PT08.S5(O3)_roll24_mean": 855.75,
                        "PT08.S5(O3)_roll24_std": 261.3274,
                        "T_roll3_mean": 9.9333,
                        "T_roll3_std": 0.3215,
                        "T_roll24_mean": 10.4125,
                        "T_roll24_std": 1.1494,
                        "RH_roll3_mean": 67.6667,
                        "RH_roll3_std": 3.5005,
                        "RH_roll24_mean": 62.2083,
                        "RH_roll24_std": 7.9871,
                        "AH_roll3_mean": 0.8273,
                        "AH_roll3_std": 0.0263,
                        "AH_roll24_mean": 0.7796,
                        "AH_roll24_std": 0.0449,
                        "hora_sin": -1.0,
                        "hora_cos": -0.0,
                        "dia_sin": 0.4339,
                        "dia_cos": -0.901,
                        "mes_sin": 0.866,
                        "mes_cos": 0.5,
                        "es_finde": 0.0,
                        "horizonte": 24.0
                    }
                }
            ]
        }
    }

class Prediccion(BaseModel):
    """Respuesta del modelo para una observación."""
    prediccion: float = Field(..., description='Concentración de NO2 prevista, en µg/m³')
    inferior: float = Field(..., description='Extremo inferior del intervalo de predicción')
    superior: float = Field(..., description='Extremo superior del intervalo de predicción')
    prob_superacion: float = Field(..., description='Probabilidad de superar los 200 µg/m³')
    alerta: bool = Field(..., description='Si la probabilidad supera el umbral de alerta')

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prediccion": 148.7,
                    "inferior": 85.1,
                    "superior": 212.3,
                    "prob_superacion": 0.141,
                    "alerta": True
                }
            ]
        }
    }

@app.get("/", include_in_schema=False)
def raiz():
    """Redirige a la documentación interactiva."""
    return RedirectResponse(url="/docs")

@app.get('/health')
def health():
    """Comprueba que el servicio está vivo y el modelo se carga."""
    try:
        _, _, _, meta = serve.load_model()
        return {
            'estado': 'ok',
            'modelo': meta['nombre'],
            'creado': meta['creado'],
            'columnas': meta['n_columnas'],
            'horizontes': meta['horizontes'],
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f'modelo no disponible: {e}')


@app.post('/predict', response_model=Prediccion)
def predict(medicion: Medicion):
    """Devuelve predicción, intervalo y probabilidad de superación."""
    try:
        entrada = pd.DataFrame([medicion.variables])
        resultado = serve.predict(entrada)
        return resultado.iloc[0].to_dict()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))