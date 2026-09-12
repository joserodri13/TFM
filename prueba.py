from tfm_airquality import model as md
from tfm_airquality.clean import clean
from tfm_airquality.features import build_features
from tfm_airquality.load import load_airquality_data

df, _ = clean(load_airquality_data())
tabla = build_features(df)
cols = md.feature_columns(tabla, 'A')

print('total:', len(cols))
print()
print('retardos  :', len([c for c in cols if '_lag' in c]))
print('ventanas  :', len([c for c in cols if '_roll' in c]))
print('calendario:', len([c for c in cols if c in
      ['hora_sin','hora_cos','dia_sin','dia_cos','mes_sin','mes_cos','es_finde']]))
print()
print('el resto:')
for c in cols:
    if '_lag' not in c and '_roll' not in c:
        print(' ', c)