import pandas as pd

#Cargamos el dataset y vemos algunos parámetros
df = pd.read_csv('data/raw/AirQuality.csv', delimiter=';', decimal=',')
print("Dimensiones:", df.shape)
print()
print("Columnas:", df.columns.tolist())
print()
print(df.head())
print(df.isna().sum())

# Eliminar columnas vacias y nulos
df = df.dropna(axis=1, how='all')
df = df.dropna(axis=0, subset=['Date', 'Time'])
print("Dimensiones:", df.shape)

# Union de Date y Time en una sola columna de fecha (DateTime). Asignar esa columna como índice y ordenar por fecha
df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%d/%m/%Y %H.%M.%S')
df = df.drop(['Date', 'Time'], axis=1)
df = df.set_index('DateTime')
df = df.sort_index()
print(df.head())