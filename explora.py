import pandas as pd
df = pd.read_csv('data/raw/AirQuality.csv', delimiter=';', decimal=',')
print("Dimensiones:", df.shape)
print()
print("Columnas:", df.columns.tolist())
print()
print(df.head())