import pandas as pd
import numpy as np
import tfm_airquality.load as load

df = load.load_airquality_data().replace(-200, np.nan)


def longitudes_rachas(serie):
    """Devuelve la longitud de cada racha de huecos consecutivos."""
    es_nulo = serie.isna()
    if not es_nulo.any():
        return pd.Series(dtype=int)
    grupos = (es_nulo != es_nulo.shift()).cumsum()
    return grupos[es_nulo].value_counts()


for col in df.columns:
    L = longitudes_rachas(df[col])
    print(f"\n=== {col} ===")
    print(f"ausentes: {int(df[col].isna().sum())} ({100*df[col].isna().mean():.1f}%)")
    if len(L) == 0:
        continue
    print(f"rachas: {len(L)} | máxima: {int(L.max())} h")
    print("longitudes:", L.value_counts().sort_index().to_dict())