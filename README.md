# TFM — Predicción de NO₂ a 24-48 horas a partir de sensores de óxido metálico

Trabajo Fin de Máster en Big Data, Data Science e Inteligencia Artificial (UCM).
Modalidad 1: análisis de un conjunto de datos.

---

## El problema

La vigilancia de la calidad del aire se apoya en analizadores certificados, que
emplean métodos de referencia normalizados (quimioluminiscencia en el caso del
NO₂) y requieren infraestructura, mantenimiento y calibración periódica. Los
dispositivos multisensor de óxido metálico son una tecnología distinta, mucho
más ligera, que permitiría desplegar un número mayor de puntos de medida.

La pregunta que aborda este trabajo es si un nodo equipado únicamente con
sensores de óxido metálico puede anticipar, con 24 a 48 horas de antelación, la
concentración de NO₂ que mediría un analizador certificado situado en el mismo
punto, con precisión suficiente para fundamentar decisiones operativas como la
activación de protocolos de restricción de tráfico.

El obstáculo no es acertar hoy, sino **seguir acertando dentro de seis meses**.
En este mismo conjunto de datos se ha medido que la relación entre la señal de
los sensores y la concentración de referencia se desplaza entre un 27 % y un
94 % al comparar el mismo mes de años consecutivos. Por eso el trabajo no
termina en un modelo, sino en un sistema con monitorización de deriva y
política de reentrenamiento.

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
- Ese límite se supera en 386 horas, el 5,0 % de las observadas: hay evento que
  predecir, y es lo bastante infrecuente para resultar interesante
- Es una medición independiente del analizador de referencia
- Es el contaminante sobre el que las ciudades activan protocolos reales

Variables descartadas como objetivo:

| Variable | Motivo |
|---|---|
| `NMHC(GT)` | 90,2 % de valores ausentes, con una racha de 8.126 horas seguidas |
| `CO(GT)` | Su umbral legal (media octohoraria > 10 mg/m³) no se supera ni una vez |
| `C6H6(GT)` | No es una medición: es una transformación de `PT08.S2` (ver hallazgos) |
| `NOx(GT)` | Sin límite legal propio; se conserva como objetivo secundario |

---

## Los dos escenarios de despliegue

El trabajo compara dos situaciones para cuantificar qué se pierde al prescindir
del analizador de referencia:

- **Escenario A (referencia).** Se predice el NO₂ disponiendo del histórico del
  analizador certificado. Es el techo de rendimiento alcanzable.
- **Escenario B (operativo).** Se predice empleando únicamente el histórico de
  los cinco sensores de óxido metálico y la meteorología de placa. Corresponde
  a un nodo que no lleva analizador.

La diferencia entre ambos está anticipada por los datos: la autocorrelación del
NO₂ a 24 horas es 0,708, mientras que la correlación de la mejor variable de
sensor al mismo horizonte es 0,411. El escenario A puede explotar la primera y
el B no.

---

## Metodología de evaluación

En series temporales no se puede repartir el dato al azar: entrenar con datos
posteriores a los de evaluación equivale a mirar el futuro, y produce métricas
excelentes y falsas.

Se emplea **partición temporal estricta** con corte el 1 de enero de 2005:
entrenamiento con marzo-diciembre de 2004, evaluación con enero-abril de 2005.
El periodo de test cae en invierno, la estación con más episodios de NO₂
elevado. Se aplica además un **embargo de 48 horas** —el horizonte máximo—
antes del corte, para que ninguna fila de entrenamiento tenga su valor objetivo
dentro del periodo de evaluación.

Cada modelo se compara contra **modelos de referencia** (persistencia y
estacionalidad diaria y semanal) mediante *skill score*. Un modelo que no supere
a "mañana como hoy a la misma hora" no aporta valor, por sofisticado que sea.

**El listón a batir es un MAE medio de 35,68 µg/m³** sobre los 48 horizontes,
correspondiente al mejor modelo de referencia en cada uno de ellos.

---

## El pipeline

El proyecto se construye como una cadena de estaciones. Cada una recibe algo,
hace una cosa concreta y se la pasa a la siguiente. El nombre de cada estación
coincide con el de su módulo de código.

| # | Estación | Módulo | Qué produce | Estado |
|---|---|---|---|---|
| 1 | Load | `load.py` | Tabla con sello temporal, ordenada | **Hecha** |
| 2 | Validate | `validate.py` | Data contract verificado | **Hecha** |
| 3 | Clean | `clean.py` | Huecos tratados, columnas descartadas | **Hecha** |
| 4 | EDA | `eda.py` | Gráficos y hallazgos documentados | **Hecha** |
| 5 | Features | `features.py` | Retardos, medias móviles, calendario | **Hecha** |
| 6 | Split | `split.py`, `metrics.py`, `baselines.py`, `evaluate.py` | Baselines y listón a batir | **Hecha** |
| 7 | Model | `model.py` | Escalera de modelos comparados | **Hecha** |
| 8 | Explain | `explain.py` | SHAP y contraste con la química de sensores | **Hecha**  |
| 9 | Uncertainty | `uncertainty.py` | Intervalos y probabilidad de superar umbral | **Hecha**  |
| 10 | Serve | `serve.py` | API que recibe datos y devuelve predicción | **Hecha**  |
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

## Hallazgos

Todos verificados con el código del proyecto.

**Sobre el origen de los datos**

- El rango real va del 10/03/2004 al 04/04/2005. La documentación oficial
  indica "marzo de 2004 a febrero de 2005", por lo que hay casi dos meses que
  la descripción del origen no menciona.
- La serie horaria está completa y sin saltos: 9.357 horas y 9.357 filas, sin
  duplicados.

**Sobre la calidad del dato**

- Los valores ausentes están dominados por paradas prolongadas del equipo, no
  por ruido disperso: en `NO2(GT)`, 21 averías de 12 horas o más concentran
  1.316 de las 1.642 horas perdidas.
- Los huecos de una sola hora corresponden al **ciclo de autocalibración del
  analizador**: 304 de los 320 se producen a las 03:00 en `NO2(GT)` y
  `NOx(GT)`, y 131 de 145 a las 04:00 en `CO(GT)`.
- **`C6H6(GT)` no es una medición del analizador** pese a llevar el sufijo
  `(GT)`. Es una transformación monótona de `PT08.S2` redondeada a un decimal:
  correlación de 0,98, mismo patrón de ausencias que la placa de sensores, 407
  valores distintos frente a 1.246 del sensor, y relación monótona creciente en
  la que 1.078 de los 1.245 valores del sensor tienen un único valor de benceno
  asociado.

**Sobre la estructura temporal**

- Perfil horario con mínimo de 58,6 µg/m³ a las 04:00 y máximo de 150,1 a las
  19:00: el pico casi triplica el valle.
- Perfil semanal creciente de lunes a viernes, con el domingo un 26 % por
  debajo del viernes.
- Autocorrelación de 0,900 a 1 hora, 0,708 a 24 y 0,646 a 168. Los tres máximos
  locales justifican los retardos construidos.

**Sobre los episodios de superación**

- Las 386 superaciones se agrupan en 136 episodios, de 2,8 horas de duración
  media y 18 de máxima. El 42 % dura tres horas o más.
- Ninguna superación entre las 03:00 y las 07:00. El 41 % se concentra entre
  las 18:00 y las 21:00.
- Febrero acumula 160 superaciones, el 41 % del total. De abril a octubre
  prácticamente no se registra ninguna.

**Sobre la deriva**

- La relación entre la señal de los sensores y la concentración de referencia
  se desplaza entre un 27 % y un 94 % al comparar marzo de 2004 con marzo de
  2005, meses con idéntico régimen estacional.
- **`PT08.S4`, el sensor nominalmente dedicado al NO₂, presenta una correlación
  global de solo 0,16 con el objetivo, pero correlaciones mensuales de hasta
  0,835.** Es un caso de paradoja de Simpson: la relación existe dentro de cada
  mes, pero el nivel base se desplaza lo suficiente entre meses como para
  destruirla a escala global.

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
    reports/figuras/      figuras generadas, ignorado por git
    data/                 datos, ignorado por git

---

## Reproducibilidad

- Los datos no se versionan en git: el repositorio contiene código, no ficheros
  de datos
- Cada decisión de diseño queda registrada con su fecha y su motivo en
  `docs/decisiones.md`
- Cada estación del pipeline tiene sus propias pruebas automáticas, ejecutables
  con `pytest` desde la raíz del proyecto

## Ejecutar el sistema

API REST:

    uvicorn tfm_airquality.api:app
    # documentación en http://127.0.0.1:8000/docs

Panel de visualización:

    streamlit run app.py

## Convenciones

- Identificadores de código (ficheros, funciones, variables) en inglés
- Comentarios, documentación y diario de decisiones en español
- Los nombres de las estaciones coinciden con los de sus módulos

---

## Autoría

Trabajo individual.
Tutores: Carlos Ortega y Santiago Mota.
