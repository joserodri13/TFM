import pandas as pd
import numpy as np
import tfm_airquality.load as load

from tfm_airquality.load import load_airquality_data
from tfm_airquality.clean import sentinel_to_nan, gap_runs

df = load_airquality_data()
limpio = sentinel_to_nan(df)
print((df == -200).sum().sum(), "->", limpio.isna().sum().sum())

df = sentinel_to_nan(load_airquality_data())
r = gap_runs(df['NO2(GT)'])
print(len(r), "rachas")
print(r)