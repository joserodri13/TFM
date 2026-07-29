# TFM — Predicción de NO₂ a 24-48 horas con sensores de bajo coste

Trabajo Fin de Máster en Big Data, Data Science e Inteligencia Artificial (UCM).
Modalidad 1: análisis de un conjunto de datos.

---

## El problema de negocio

Un analizador de calidad del aire certificado cuesta decenas de miles de euros.
Un nodo con sensores de óxido metálico cuesta dos órdenes de magnitud menos.

Si un modelo consigue predecir con antelación suficiente la concentración de NO₂
*equivalente a la de un analizador certificado* a partir de sensores baratos, un
ayuntamiento puede pasar de tres estaciones de medida a cincuenta puntos con el
mismo presupuesto, y anticipar con 24-48 horas la activación de protocolos de
restricción de tráfico.

El obstáculo real no es acertar hoy, sino **seguir acertando dentro de seis
meses**: los sensores derivan con el tiempo. Por eso el trabajo no termina en un
modelo, sino en un sistema con monitorización de deriva y política de
reentrenamiento.

---

## Los datos

**Air Quality Data Set** — UCI Machine Learning Repository.

9.357 registros horarios tomados en una ciudad italiana entre marzo de 2004 y
abril de 2005, con:

- 5 sensores de óxido metálico (PT08.S1 a PT08.S5), que devuelven señal
  eléctrica en unidades arbitrarias
- Meteorología de placa: temperatura, humedad relativa y humedad absoluta
- Mediciones de un analizador certificado colocado en el mismo emplazamiento,
  identificadas con el sufijo `(GT)` (*ground truth*), en unidades físicas
  reales

Los valores ausentes vienen marcados con el valor -200.

### Derechos de uso

Uso exclusivamente investigador; los usos comerciales están excluidos. Citación
obligatoria:

> De Vito, S. et al. *Sensors and Actuators B: Chemical*, vol. 129, n.º 2, 2008.

El conjunto no contiene datos de carácter personal, por lo que el RGPD no
resulta de aplicación.

---

## Qué se predice y por qué

**Variable objetivo:** `NO2(GT)`, a horizontes de 1 a 48 horas.

Motivos de la elección:

- Está expresada en µg/m³, directamente comparable con el valor límite horario
  europeo de 200 µg/m³
- Ese límite se supera en una minoría relevante de las horas observadas: hay
  evento que predecir, y es lo bastante infrecuente para resultar interesante
- Es una medición independiente del analizador de referencia
- Es el contaminante sobre el que las ciudades activan protocolos reales

Variables descartadas como objetivo:

| Variable | Motivo |
|---|---|
| `NMHC(GT)` | Cobertura insuficiente (~90 % de valores ausentes) |
| `CO(GT)` | Su umbral legal no se supera en todo el periodo |
| `C6H6(GT)` | Indicios de estar derivada del sensor, no medida (ver hallazgos) |
| `NOx(GT)` | Sin límite legal propio; se conserva como objetivo secundario |

---

## Los dos escenarios de despliegue

El trabajo compara dos situaciones para cuantificar el coste real de sustituir
un equipo certificado por sensores baratos:

- **Escenario A (referencia).** Se predice el NO₂ disponiendo del histórico del
  analizador certificado. Es el techo de rendimiento alcanzable.
- **Escenario B (operativo).** Se predice usando únicamente el histórico de los
  cinco sensores de bajo coste. Es el nodo real de una red densa: no lleva
  analizador.

La pregunta de negocio es cuantificable: *¿cuánta precisión se pierde al
sustituir un analizador certificado por un nodo de bajo coste, y sigue siendo
suficiente para decidir una restricción de tráfico con 24 horas de antelación?*

---

## Metodología de evaluación

En series temporales no se puede repartir el dato al azar: entrenar con datos
posteriores a los de evaluación equivale a mirar el futuro, y produce métricas
excelentes y falsas.

Se emplea **partición temporal estricta**: entrenamiento con los primeros ~9
meses (marzo-diciembre 2004), evaluación con los últimos ~3 meses y medio
(enero-abril 2005). El periodo de test cae en invierno, la estación con más
episodios de NO₂ elevado.

Cada modelo se compara contra **modelos de referencia** (persistencia y
estacionalidad diaria y semanal) mediante *skill score*. Un modelo que no supere
a "mañana como hoy a la misma hora" no aporta valor, por sofisticado que sea.

---

## El pipeline

El proyecto se construye como una cadena de estaciones. Cada una recibe algo,
hace una cosa concreta y se la pasa a la siguiente. El nombre de cada estación
coincide con el de su módulo de código.

| # | Estación | Módulo | Qué produce | Estado |
|---|---|---|---|---|
| 1 | Load | `load.py` | Tabla con sello temporal, ordenada | **Hecha** |
| 2 | Validate | `validate.py` | Contrato de datos verificado | Pendiente |
| 3 | Clean | `clean.py` | Huecos tratados, columnas descartadas | Pendiente |
| 4 | EDA | `eda.py` | Gráficos y hallazgos documentados | Pendiente |
| 5 | Features | `features.py` | Retardos, medias móviles, calendario | Pendiente |
| 6 | Split | `split.py`, `metrics.py`, `baselines.py` | Baselines y listón a batir | Pendiente |
| 7 | Model | `model.py` | Escalera de modelos comparados | Pendiente |
| 8 | Explain | `explain.py` | SHAP y contraste con la química de sensores | Pendiente |
| 9 | Uncertainty | `uncertainty.py` | Intervalos y probabilidad de superar umbral | Pendiente |
| 10 | Serve | `serve.py` | API que recibe datos y devuelve predicción | Pendiente |
| 11 | Monitor | `monitor.py` | Vigilancia de degradación y reentrenamiento | Pendiente |
| 12 | Memoria | — | Informe de 20 caras orientado a negocio | Pendiente |
| 13 | Entrega | — | MP4 de 5 minutos y checklist de la guía | Pendiente |

### Correspondencia con las fases exigidas por la guía del TFM

| Fase de la guía | Estación |
|---|---|
| i. Análisis descriptivo | 4 (EDA) |
| ii. Transformaciones | 3 (Clean) y 5 (Features) |
| iii. Modelos de predicción | 7 (Model) |
| iv. Interpretabilidad | 8 (Explain) |
| v. Informe final para negocio | 12 (Memoria) |
| vi. Productivización | 10 (Serve) y 11 (Monitor) |

---

## Hallazgos preliminares

Observaciones detectadas en una exploración inicial, **pendientes de verificar
con el código del proyecto** en la estación 4 (EDA):

- **El sensor `PT08.S4`, nominalmente dedicado al NO₂, parece ser el menos
  informativo sobre el NO₂.** El más informativo sería el de ozono, `PT08.S5`.
  De confirmarse, sería la sensibilidad cruzada documentada por los autores del
  dataset, y el eje de la sección de interpretabilidad.
- **`C6H6(GT)` presenta indicios de estar derivada del sensor `PT08.S2`** en
  lugar de medida por el analizador: su patrón de valores ausentes coincidiría
  hora a hora con el de la placa de sensores, y su correlación con el sensor
  sería muy alta.
- **Los valores ausentes parecen estar dominados por unas pocas paradas
  prolongadas del equipo**, no por ruido disperso.

### Verificado

- **El rango real de los datos va del 10/03/2004 al 04/04/2005.** La
  documentación oficial del dataset indica "marzo de 2004 a febrero de 2005",
  por lo que hay casi dos meses que la descripción del origen no menciona.
- **La serie horaria está completa y sin saltos**: el rango temporal contiene
  exactamente 9.357 horas y la tabla tiene exactamente 9.357 filas, sin
  duplicados.

---

## Instalación

Requiere Python 3.12.

    git clone https://github.com/joserodri13/TFM.git
    cd TFM

    python -m venv .venv
    .venv\Scripts\activate        # Windows
    source .venv/bin/activate     # macOS / Linux

    pip install -e ".[dev]"

Los datos **no** están en este repositorio. Descarga `AirQuality.csv` del UCI
Machine Learning Repository y colócalo en `data/raw/`.

---

## Estructura del repositorio

    src/tfm_airquality/   código del pipeline, una estación por módulo
    tests/                pruebas automáticas del código
    docs/                 diario de decisiones y borradores de la memoria
    notebooks/            exploración; el código estable se muda a src/
    data/                 datos, ignorado por git

---

## Reproducibilidad

- Los datos no se versionan en git: el repositorio contiene código, no ficheros
  de datos
- Cada decisión de diseño queda registrada con su fecha y su motivo en
  `docs/decisiones.md`
- Cada estación del pipeline tiene sus propias pruebas automáticas, ejecutables
  con `pytest` desde la raíz del proyecto

---

## Convenciones

- Identificadores de código (ficheros, funciones, variables) en inglés
- Comentarios, documentación y diario de decisiones en español
- Los nombres de las estaciones coinciden con los de sus módulos

---

## Autoría

Trabajo individual.
Tutores: Carlos Ortega y Santiago Mota.