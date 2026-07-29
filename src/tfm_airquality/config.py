from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

# Ruta construida a partir de la ubicacion de este fichero, no del directorio
# desde el que se ejecuta Python. Asi funciona igual desde la raiz, desde
# tests/ o desde notebooks/.
RAIZ = Path(__file__).resolve().parents[2]
PATH_CSV = RAIZ / "data" / "raw" / "AirQuality.csv"

# ---------------------------------------------------------------------------
# Columnas
# ---------------------------------------------------------------------------

# Mediciones del analizador certificado de referencia ("ground truth"). Son
# las unicas columnas con significado fisico y comparables con la normativa.
GT_COLUMNS = ['CO(GT)', 'NMHC(GT)', 'C6H6(GT)', 'NOx(GT)', 'NO2(GT)']

# Respuestas crudas de los cinco sensores de oxido metalico. Son senales
# electricas en unidades arbitrarias, NO concentraciones. Son entradas del
# modelo, nunca objetivos.
SENSOR_COLUMNS = [
    'PT08.S1(CO)',
    'PT08.S2(NMHC)',
    'PT08.S3(NOx)',
    'PT08.S4(NO2)',
    'PT08.S5(O3)',
]

# Meteorologia registrada por la propia placa de sensores.
MET_COLUMNS = ['T', 'RH', 'AH']

# Las 13 columnas que debe tener la tabla tras la estacion 1 (Load).
EXPECTED_COLUMNS = GT_COLUMNS + SENSOR_COLUMNS + MET_COLUMNS

# Columnas descartadas del conjunto de trabajo.
# NMHC(GT): 90,2 % de valores ausentes, con una unica racha de 8.126 horas
# seguidas (el sensor estuvo apagado casi 340 dias). No hay nada que modelar.
UNUSABLE_COLUMNS = ['NMHC(GT)']

# ---------------------------------------------------------------------------
# Variable objetivo
# ---------------------------------------------------------------------------

# NO2(GT): esta en ug/m3 y es comparable con el limite horario europeo de 200,
# que supera en 386 horas; es medida independiente del analizador; y es el
# contaminante sobre el que las ciudades activan protocolos reales.
TARGET = 'NO2(GT)'

# Objetivo secundario para un eventual modelo multi-salida.
TARGET_SECONDARY = 'NOx(GT)'

# ---------------------------------------------------------------------------
# Formato del fichero de origen
# ---------------------------------------------------------------------------

# El CSV viene en formato europeo. Leerlo con los valores por defecto de
# pandas no lanza ningun error: devuelve una tabla de una sola columna.
CSV_DELIMITER = ';'
CSV_DECIMAL = ','

# Formato de fecha declarado explicitamente. La inferencia automatica de
# pandas interpreta '10/03/2004' como formato americano (mes/dia).
DATE_FORMAT = '%d/%m/%Y %H.%M.%S'

# Marcador de dato ausente del dataset. Mientras siga siendo un numero, toda
# media, correlacion o grafico que lo toque estara contaminado sin aviso.
MISSING_SENTINEL = -200

# ---------------------------------------------------------------------------
# Estacion 2: data contract
# ---------------------------------------------------------------------------

# Cotas de plausibilidad: lo que seria imposible medir. NO son limites
# legales. Superar el limite legal es un episodio de contaminacion, no un
# error de medicion, y detectarlo es el objetivo del proyecto: NO2 supera los
# 200 ug/m3 en 386 horas de este mismo fichero.
PLAUSIBLE_RANGES = {
    # Meteorologia: limites fisicos.
    'T': (-15.0, 50.0),          # °C. Extremos historicos en Italia.
    'RH': (0.0, 100.0),          # %. Definicion de humedad relativa.
    'AH': (0.0, 5.0),            # max. observado 2,2.

    # Analizador de referencia. Limite legal entre parentesis, solo como
    # referencia: la cota es muy superior a proposito.
    'CO(GT)': (0.0, 50.0),       # mg/m3 (legal 8h: 10). Max. obs. 11,9.
    'C6H6(GT)': (0.0, 200.0),    # ug/m3 (legal anual: 5). Max. obs. 63,7.
    'NOx(GT)': (0.0, 3000.0),    # ppb, sin limite legal propio. Max. obs. 1479.
    'NO2(GT)': (0.0, 1000.0),    # ug/m3 (legal horario: 200). Max. obs. 340.
    'NMHC(GT)': (0.0, 3000.0),   # ug/m3. Max. obs. 1189.

    # Sensores MOX: senal electrica en unidades arbitrarias. La cota responde
    # al rango del hardware, no a normativa alguna. Max. obs. 2040 a 2775.
    'PT08.S1(CO)': (0.0, 4000.0),
    'PT08.S2(NMHC)': (0.0, 4000.0),
    'PT08.S3(NOx)': (0.0, 4000.0),
    'PT08.S4(NO2)': (0.0, 4000.0),
    'PT08.S5(O3)': (0.0, 4000.0),
}

# Numero de filas esperado. Informativo: puede cambiar legitimamente si se
# usa otra version del dataset.
EXPECTED_ROWS = 9357

# Porcentaje minimo de valores observados del objetivo para que modelar tenga
# sentido. NMHC(GT), con un 9,8 %, es el caso que este umbral descarta.
MIN_TARGET_COVERAGE = 50.0

# ---------------------------------------------------------------------------
# Estacion 3: clean
# ---------------------------------------------------------------------------

# Longitud maxima (en horas) de una racha de huecos que se considera
# interpolable. Se midio el error de la interpolacion tapando tramos con dato
# observado: 12,4 ug/m3 a 2 horas frente a 19,3 a 5 horas, cifra ya comparable
# al error del modelo de referencia por persistencia. Ampliar el umbral a 5
# recuperaria solo 12 horas mas sobre 9.357.
MAX_INTERPOLABLE_GAP = 2