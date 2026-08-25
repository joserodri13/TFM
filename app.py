"""
Panel de vigilancia de NO2.

Ejecutar con:  streamlit run app.py
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from tfm_airquality import config, model as md, serve
from tfm_airquality.clean import clean
from tfm_airquality.features import build_features
from tfm_airquality.load import load_airquality_data
from tfm_airquality.split import split_temporal

st.set_page_config(page_title='Vigilancia de NO₂', layout='wide',
                   page_icon='🌫️')

# Paleta: azul para lo observado, naranja para lo predicho, rojo para el
# limite legal. Se mantiene en todos los elementos del panel.
AZUL = '#1f77b4'
NARANJA = '#ff7f0e'
ROJO = '#d62728'
VERDE = '#2ca02c'

st.markdown("""
<style>
    .stMetric {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 14px;
    }
    div[data-testid="stMetricValue"] { font-size: 1.7rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def cargar_datos():
    """Se cachea: recalcular en cada interacción sería inviable."""
    df, _ = clean(load_airquality_data())
    tabla = build_features(df)
    _, test = split_temporal(tabla)
    cols = md.feature_columns(tabla, 'A')
    return df, test[cols + ['y']].dropna(), cols


df, test, cols = cargar_datos()

# ---------------------------------------------------------------------------
# Cabecera
# ---------------------------------------------------------------------------

st.title('🌫️ Vigilancia de NO₂')
st.caption('Predicción a 1-48 horas con intervalo de confianza y probabilidad '
           f'de superación del límite legal de {config.UMBRAL_LEGAL:.0f} µg/m³')

# ---------------------------------------------------------------------------
# Controles
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header('Configuración')

    fechas = sorted({t.date() for t in test.index})
    dia = st.date_input('Fecha de referencia',
                        value=fechas[len(fechas) // 2],
                        min_value=fechas[0], max_value=fechas[-1],
                        format='DD/MM/YYYY')

    horas_dia = sorted({t.hour for t in test.index if t.date() == dia})
    if not horas_dia:
        st.warning('No hay datos para ese día.')
        st.stop()

    hora = st.selectbox('Hora', horas_dia,
                        index=min(12, len(horas_dia) - 1),
                        format_func=lambda h: f'{h:02d}:00')

    momento = pd.Timestamp(dia) + pd.Timedelta(hours=hora)

    horizonte = st.radio('Horizonte de predicción',
                         config.HORIZONTES, index=3, horizontal=True,
                         format_func=lambda h: f'{h} h')

    st.divider()
    st.markdown(
        f"""
        **Parámetros del sistema**

        - Umbral de alerta: {config.UMBRAL_ALERTA:.0%} de probabilidad
        - Cobertura del intervalo: {config.COBERTURA:.0%}
        - Límite legal: {config.UMBRAL_LEGAL:.0f} µg/m³ (horario)
        """
    )

fila = test[(test.index == momento) & (test['horizonte'] == horizonte)]

if len(fila) == 0:
    st.warning(f'No hay datos para el {momento:%d/%m/%Y %H:%M} '
               f'con horizonte de {horizonte} horas.')
    st.stop()

r = serve.predict(fila[cols]).iloc[0]
real = fila['y'].iloc[0]
objetivo = momento + pd.Timedelta(hours=horizonte)

# ---------------------------------------------------------------------------
# Aviso principal
# ---------------------------------------------------------------------------

if r['alerta']:
    st.error(
        f'### ⚠️ ALERTA\n'
        f'Riesgo de superación del límite legal el '
        f'**{objetivo:%d/%m/%Y}** a las **{objetivo:%H:%M}** — '
        f'probabilidad estimada del **{r["prob_superacion"]:.1%}**'
    )
else:
    st.success(
        f'### ✅ Sin alerta\n'
        f'Para el **{objetivo:%d/%m/%Y}** a las **{objetivo:%H:%M}** — '
        f'probabilidad estimada del **{r["prob_superacion"]:.1%}**'
    )

# ---------------------------------------------------------------------------
# Indicadores
# ---------------------------------------------------------------------------

m1, m2, m3, m4 = st.columns(4)

m1.metric('Predicción', f"{r['prediccion']:.0f} µg/m³")
m2.metric(f"Intervalo {config.COBERTURA:.0%}",
          f"{r['inferior']:.0f} – {r['superior']:.0f}",
          help='Rango dentro del cual se espera que caiga el valor real')
m3.metric('Prob. de superar el límite', f"{r['prob_superacion']:.1%}")

error = real - r['prediccion']
dentro = r['inferior'] <= real <= r['superior']
m4.metric('Valor real observado', f'{real:.0f} µg/m³',
          delta=f'{error:+.0f} respecto a lo predicho', delta_color='off',
          help='Dentro del intervalo' if dentro else 'Fuera del intervalo')

# ---------------------------------------------------------------------------
# Grafico principal
# ---------------------------------------------------------------------------

st.subheader('Contexto temporal')

ventana = df.loc[
    momento - pd.Timedelta(hours=72):objetivo + pd.Timedelta(hours=12),
    config.TARGET
]

fig = go.Figure()

# Zona de riesgo por encima del limite legal
fig.add_hrect(y0=config.UMBRAL_LEGAL, y1=max(400, ventana.max() * 1.1),
              fillcolor=ROJO, opacity=0.06, line_width=0)

# Banda del intervalo sobre el instante objetivo
fig.add_trace(go.Scatter(
    x=[objetivo, objetivo], y=[r['inferior'], r['superior']],
    mode='lines', line=dict(color=NARANJA, width=18),
    opacity=0.3, name=f'Intervalo {config.COBERTURA:.0%}',
    hovertemplate='%{y:.0f} µg/m³<extra></extra>',
))

fig.add_trace(go.Scatter(
    x=ventana.index, y=ventana.values, mode='lines',
    name='NO₂ observado', line=dict(color=AZUL, width=2.5),
    hovertemplate='%{x|%d/%m %H:%M}<br>%{y:.0f} µg/m³<extra></extra>',
))

fig.add_trace(go.Scatter(
    x=[objetivo], y=[r['prediccion']], mode='markers',
    name='Predicción',
    marker=dict(color=NARANJA, size=16, symbol='diamond',
                line=dict(color='white', width=2)),
    hovertemplate='Predicción: %{y:.0f} µg/m³<extra></extra>',
))

fig.add_trace(go.Scatter(
    x=[objetivo], y=[real], mode='markers', name='Valor real',
    marker=dict(color=ROJO, size=13, symbol='x',
                line=dict(color='white', width=1)),
    hovertemplate='Real: %{y:.0f} µg/m³<extra></extra>',
))

fig.add_trace(go.Scatter(
    x=[momento], y=[df.loc[momento, config.TARGET]], mode='markers',
    name='Instante de referencia',
    marker=dict(color=VERDE, size=13,
                line=dict(color='white', width=2)),
    hovertemplate='Ahora: %{y:.0f} µg/m³<extra></extra>',
))

fig.add_hline(y=config.UMBRAL_LEGAL, line_dash='dash', line_color=ROJO,
              line_width=2,
              annotation_text=f'Límite legal ({config.UMBRAL_LEGAL:.0f} µg/m³)',
              annotation_position='top left')

fig.add_vline(x=momento, line_dash='dot', line_color='gray', line_width=1)

fig.update_layout(
    height=440, hovermode='x unified',
    xaxis_title='', yaxis_title='NO₂ (µg/m³)',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0),
    margin=dict(t=50, b=20, l=0, r=0),
    plot_bgcolor='white',
)
fig.update_xaxes(showgrid=True, gridcolor='#eee')
fig.update_yaxes(showgrid=True, gridcolor='#eee')

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Todos los horizontes
# ---------------------------------------------------------------------------

st.subheader('Predicción a todos los horizontes')

filas_h = test[test.index == momento]

if len(filas_h) == 0:
    st.info('No hay predicciones disponibles para este instante.')
else:
    pred_h = serve.predict(filas_h[cols])
    pred_h['horizonte'] = filas_h['horizonte'].values
    pred_h['real'] = filas_h['y'].values
    pred_h = pred_h.sort_values('horizonte')

    faltan = set(config.HORIZONTES) - set(pred_h['horizonte'])
    if faltan:
        st.caption(f'Sin datos para los horizontes: {sorted(faltan)} '
                   '(el valor real correspondiente no fue registrado)')

    tabla = pred_h[['horizonte', 'prediccion', 'inferior', 'superior',
                    'prob_superacion', 'alerta', 'real']].reset_index(drop=True)
    tabla['acierto'] = (
        (tabla['real'] > config.UMBRAL_LEGAL) == tabla['alerta']
    )
    tabla.columns = ['Horizonte (h)', 'Predicción', 'Mínimo', 'Máximo',
                     'Prob. superación', 'Alerta', 'Real', 'Acierto']

    def color_prob(v):
        if v >= config.UMBRAL_ALERTA:
            return 'background-color: #ffe5e5; color: #a00; font-weight: 600'
        return 'color: #666'

    st.dataframe(
        tabla.style
        .format({'Predicción': '{:.0f}', 'Mínimo': '{:.0f}',
                 'Máximo': '{:.0f}', 'Prob. superación': '{:.1%}',
                 'Real': '{:.0f}'})
        .map(color_prob, subset=['Prob. superación']),
        hide_index=True, use_container_width=True,
    )

    st.caption(
        'La columna *Acierto* indica si la decisión de alertar o no '
        'coincidió con lo ocurrido. El sistema no es infalible: se producen '
        'tanto falsas alarmas como episodios no advertidos.'
    )
    
# ---------------------------------------------------------------------------
# Informacion
# ---------------------------------------------------------------------------

st.divider()

with st.expander('ℹ️ Cómo interpretar este panel'):
    st.markdown(f"""
### La predicción

El modelo estima la concentración de NO₂ que habrá dentro del horizonte
seleccionado, a partir de las mediciones disponibles en el instante de
referencia: los cinco sensores del dispositivo, la meteorología, el histórico
reciente de concentraciones y variables de calendario.

**No usa información posterior al instante de referencia.** Predice el futuro
con lo que se sabe en el presente, igual que haría en operación real.

### El intervalo de confianza

El intervalo indica el rango dentro del cual se espera que caiga el valor real
con una probabilidad del **{config.COBERTURA:.0%}**.

Se construye midiendo los errores que el modelo cometió sobre un conjunto de
datos que no vio durante el entrenamiento (noviembre y diciembre de 2004). La
anchura es **distinta para cada horizonte**, porque la incertidumbre no es la
misma a una hora vista que a dos días:

| Horizonte | Semianchura |
|---|---|
| 1 h | ±40 µg/m³ |
| 6 h | ±68 µg/m³ |
| 12 h | ±68 µg/m³ |
| 24 h | ±62 µg/m³ |
| 48 h | ±62 µg/m³ |

Llama la atención que el intervalo a 6 y 12 horas sea más ancho que a 48. No es
un error: predecir a media jornada es más difícil que predecir a un día
completo, porque a 24 horas el ciclo diario vuelve a alinearse y la
concentración a la misma hora del día anterior es un buen indicio.

**Cobertura real medida:** entre el 80 % y el 84 % según el horizonte, por
debajo del {config.COBERTURA:.0%} nominal. La causa es que los sensores derivan
con el tiempo y el periodo de evaluación resultó más severo que el de
calibración. Es una limitación conocida y declarada del sistema.

### La probabilidad de superación

Es la probabilidad estimada de que el valor real supere los
**{config.UMBRAL_LEGAL:.0f} µg/m³** del límite legal horario europeo.

Se calcula contando qué proporción de los errores históricos del modelo,
aplicados a esta predicción, la situarían por encima del umbral. Por eso una
predicción de 176 µg/m³ puede tener un 21 % de probabilidad de superar 200: no
es que el modelo espere una superación, es que su margen de error lo hace
posible.

### El umbral de alerta

Se emite alerta cuando la probabilidad supera el **{config.UMBRAL_ALERTA:.0%}**.

Ese valor no es arbitrario. Se eligió mediante un análisis de sensibilidad al
coste de los errores: es el umbral óptimo para cualquier valoración que
considere un episodio no advertido entre 5 y 20 veces más costoso que una falsa
alarma.

Con ese umbral, el sistema detecta **51 de los 76 episodios** del periodo
evaluado (67 %), con una precisión del 39 %. Un umbral más alto reduciría las
falsas alarmas pero dejaría escapar la mayoría de los episodios.

### Limitaciones

- El sistema **no es infalible**: se producen tanto falsas alarmas como
  episodios no advertidos. La columna *Acierto* de la tabla lo refleja.
- El modelo se entrenó con 90 superaciones del umbral y se evalúa contra 271:
  no ha visto suficientes episodios invernales para anticiparlos todos.
- No dispone de predicción meteorológica futura, que es el predictor natural de
  la dispersión atmosférica a plazos de días.
- La relación entre la señal de los sensores y la concentración real se
  desplaza con el tiempo, lo que exige recalibración periódica.
- **Los huecos en la línea azul** corresponden a horas sin medición del
analizador de referencia. El conjunto tiene 1.642 horas ausentes, en su
mayoría por paradas prolongadas del equipo (21 averías concentran 1.316 de
ellas) y por el ciclo de autocalibración diario, que interrumpe la medición
a las 03:00. No se representan porque no existe dato que representar.
""")
