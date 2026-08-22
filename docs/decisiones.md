# Diario de decisiones

Registro de cada decisión de diseño, con su fecha y su motivo.

**Cómo usarlo.** Cada vez que elijas algo —un umbral, una variable, un modelo,
un tratamiento— añade una entrada antes de seguir adelante. Cuesta un minuto.

**Por qué existe.** Dentro de un mes no vas a recordar por qué descartaste una
variable ni de dónde salió un umbral concreto. Además, la memoria del TFM se
evalúa en buena medida por la calidad de las justificaciones, no por la
sofisticación de los modelos. Estas entradas se convierten casi literalmente en
párrafos de la memoria.

**Regla importante: aquí no se borra nada.** El README describe el estado
actual del proyecto y se reescribe cuando algo cambia. Este diario registra la
historia y es acumulativo. Si más adelante cambias una decisión, no edites la
entrada antigua: añade una nueva explicando el cambio y su motivo. Poder
escribir en la memoria "inicialmente se optó por X, pero al observar Y se
cambió a Z" demuestra criterio; presentar Z como si hubiera sido obvio desde el
principio, no.

---

## 2026-07-24 — Modalidad y conjunto de datos

**Decisión:** modalidad 1 de la guía (análisis de un dataset), sobre el
conjunto Air Quality del UCI Machine Learning Repository.

**Motivo:** permite recorrer el ciclo completo de modelización que exige la
guía, incluidas las fases de interpretabilidad y productivización que los
tutores señalaron como habitualmente ausentes en las propuestas presentadas.

**Riesgo asumido:** es un conjunto conocido y con abundante código público, y
la guía desaconseja explícitamente ese perfil. La estrategia de mitigación es
no competir por el lado del dato sino por el del enfoque: validación temporal
rigurosa, escenario de despliegue basado solo en sensores, tratamiento de la
deriva como eje central e intervalos de predicción.

**Pendiente:** justificar esta elección de forma explícita en la memoria.

---

## 2026-07-24 — Derechos de uso de los datos

**Decisión:** el conjunto se emplea al amparo de su licencia de uso
exclusivamente investigador. Se cita obligatoriamente De Vito et al., *Sensors
and Actuators B*, vol. 129, n.º 2, 2008.

**Motivo:** la licencia excluye los usos comerciales; un TFM académico entra
dentro del uso investigador permitido. El conjunto no contiene datos de
carácter personal, por lo que el RGPD no resulta de aplicación.

**Consecuencia:** el CSV no se redistribuye en el repositorio. Se documenta de
dónde descargarlo.

---

## 2026-07-24 — Problema y variable objetivo

**Decisión:** predicción de `NO2(GT)` a horizontes de 1 a 48 horas.

**Motivo:**

- Está expresada en µg/m³, directamente comparable con el valor límite horario
  europeo de 200 µg/m³
- Ese límite se supera en una minoría relevante de las horas observadas: hay
  evento que predecir, y es lo bastante infrecuente para resultar interesante
- Es una medición independiente del analizador de referencia
- Es el contaminante sobre el que las ciudades activan protocolos reales de
  restricción de tráfico

**Alternativas descartadas:**

| Variable | Motivo del descarte |
|---|---|
| `NMHC(GT)` | Cobertura insuficiente |
| `CO(GT)` | Su umbral legal no se supera en todo el periodo |
| `C6H6(GT)` | Indicios de estar derivada del sensor (ver entrada siguiente) |
| `NOx(GT)` | Sin límite legal propio; se conserva como objetivo secundario |

**Pendiente de verificar:** las cifras concretas de cobertura y de superación
de umbrales se confirmarán con el código propio en la estación 4 (EDA).

---

## 2026-07-24 — Sospecha sobre el benceno (preliminar)

**Decisión provisional:** `C6H6(GT)` queda fuera del conjunto de trabajo, a
reserva de confirmación.

**Motivo:** una exploración inicial sugiere que no procede del analizador de
referencia sino de una curva de calibración aplicada al sensor `PT08.S2`. Los
indicios a comprobar son tres:

1. Que su patrón de valores ausentes coincida hora a hora con el de los
   sensores y la meteorología de placa, y no con el de las demás variables del
   analizador
2. Que su correlación con `PT08.S2` sea muy alta
3. Que tenga muchos menos valores distintos que el sensor, lo que sería
   coherente con una transformación monótona redondeada

**Consecuencia si se confirma:** usarla como objetivo produciría un R²
excelente y sin ningún valor, por ser una función determinista de una de las
propias entradas. Sería un hallazgo destacable para la memoria.

**Estado:** PENDIENTE DE VERIFICAR en la estación 4 (EDA).

---

## 2026-07-24 — Dos escenarios de despliegue

**Decisión:** el trabajo compara dos situaciones.

- **Escenario A (referencia):** se predice disponiendo del histórico del
  analizador certificado. Techo de rendimiento.
- **Escenario B (operativo):** se predice usando solo el histórico de los cinco
  sensores de bajo coste.

**Motivo:** convierte el trabajo en una pregunta de negocio cuantificable
—cuánta precisión se pierde al sustituir el equipo caro por sensores baratos—
en lugar de un ejercicio de precisión sin contexto.

---

## 2026-07-24 — Estrategia de validación: partición temporal fija

**Decisión:** partición temporal estricta con corte el 1 de enero de 2005.
Entrenamiento con marzo-diciembre de 2004; evaluación con enero-abril de 2005.

**Motivo:** en series temporales, repartir el dato al azar permite al modelo
aprender del futuro para predecir el pasado, lo que produce métricas
excelentes y falsas. El corte elegido deja el periodo de test en invierno, la
estación con más episodios de NO₂ elevado.

**Alternativa descartada por ahora:** validación *walk-forward* con
reentrenamiento avanzando mes a mes. Es más realista, pero se pospone por
restricción de calendario. Puede incorporarse más adelante si hay tiempo.

---

## 2026-07-29 — Pipeline de 13 estaciones

**Decisión:** el proyecto se estructura en 13 estaciones, de forma que cada
fase exigida por la guía tenga su lugar explícito, incluidas las que no son
código (memoria y entrega).

**Motivo:** una versión anterior agrupaba varias fases y dejaba fuera del
pipeline el análisis descriptivo, la interpretabilidad y los entregables
finales. Al no estar en la lista, corrían el riesgo de quedar relegados al
final. Con 13 estaciones, nada queda huérfano.

**Correspondencia con la guía:** fase i → estación 4 (EDA); fase ii →
estaciones 3 (Clean) y 5 (Features); fase iii → estación 7 (Model); fase iv →
estación 8 (Explain); fase v → estación 12 (Memoria); fase vi → estaciones 10
(Serve) y 11 (Monitor).

---

## 2026-07-29 — Método de trabajo y repositorio

**Decisiones:**

- Repositorio en GitHub, privado durante el desarrollo. Antes de la entrega se
  dará acceso a Carlos Ortega y Santiago Mota.
- Los datos no se versionan en git. El CSV queda en local, ignorado mediante
  `.gitignore`.
- El código del pipeline se escribe en ficheros `.py` dentro de
  `src/tfm_airquality/`, no en notebooks. Los notebooks se reservan para
  exploración.
- Se trabaja directamente sobre la rama `main`, sin ramas adicionales, por
  tratarse de un trabajo individual.

**Motivo del punto sobre notebooks:** el código en `.py` es testeable e
importable, y su orden de ejecución no engaña. En un notebook, el resultado en
pantalla puede no corresponder a lo que ocurriría al ejecutarlo de arriba
abajo, lo que genera errores invisibles.

---

## 2026-07-29 — Ajuste de alcance por calendario

**Decisión:** se retiran del alcance las redes neuronales temporales y el
despliegue en la nube.

**Motivo:** entrega el 15 de septiembre con agosto no disponible, lo que deja
entre tres y cuatro semanas efectivas. Se prioriza completar el ciclo entero
frente a profundizar en un solo punto: un sistema completo y coherente puntúa
más que un modelo sofisticado dentro de un trabajo incompleto.

**No negociable:** interpretabilidad (estación 8, Explain) y monitorización
(estación 11, Monitor), por ser exactamente las fases que los tutores
señalaron como ausentes en las propuestas.

---

## 2026-07-29 — Diagnóstico del fichero de origen

**Contexto:** primera lectura del CSV antes de escribir el código de la
estación 1 (Load).

**Hallazgo principal:** el fichero viene en formato europeo, con punto y coma
como separador de campos y coma como separador decimal. Una lectura con los
valores por defecto de pandas (`pd.read_csv(ruta)`) **no lanza ningún error**:
devuelve una tabla de 9.471 filas y **una sola columna**, en la que los quince
nombres de variable quedan concatenados como si fueran el nombre de esa única
columna, y los datos como texto.

Ver `docs/capturas/01-lectura-ingenua-una-columna.png`.

**Por qué importa:** este es el tipo de fallo más peligroso en un proyecto de
datos, porque no interrumpe la ejecución. El programa termina correctamente y
devuelve un objeto válido; solo el contenido es basura. Sin una comprobación
explícita, el error puede propagarse durante horas de trabajo antes de
detectarse, o no detectarse nunca.

**Consecuencia directa:** justifica la existencia de la estación 2 (Validate)
como parada obligatoria del pipeline. No basta con que el código se ejecute sin
errores: hay que comprobar activamente que el dato leído es el esperado.

**Otras anomalías detectadas en la misma exploración:**

1. **Dos columnas fantasma.** Cada línea del fichero termina en `;;`, lo que
   induce a pandas a crear dos columnas adicionales sin nombre
   (`Unnamed: 15`, `Unnamed: 16`), completamente vacías.
2. **Ciento catorce filas vacías al final del fichero.** El fichero contiene
   9.471 líneas de datos frente a los 9.357 registros que declara la
   documentación del dataset. Las 114 sobrantes no tienen fecha ni hora ni
   ningún valor.
3. **Discrepancia con la documentación del origen.** La descripción del
   dataset indica que las mediciones abarcan de marzo de 2004 a febrero de
   2005. Pendiente de confirmar con el código propio si el rango real coincide.

**Decisión:** la lectura se realiza especificando explícitamente `sep=';'` y
`decimal=','`. Las columnas fantasma y las filas vacías se eliminan en la
propia estación de carga, por tratarse de artefactos del formato del fichero
y no de datos ausentes reales.

**Descartado:** especificar `encoding='latin-1'`. Se comprobó que el resultado
de la lectura es idéntico con y sin ese parámetro, ya que los nombres de
columna del fichero no contienen caracteres acentuados. Se omite para no
sugerir en el código un problema de codificación que no existe.

---

## 2026-07-29 — Estación 1 (Load) completada

**Resultado:** `src/tfm_airquality/load.py` con la función
`load_airquality_data()`, que devuelve una tabla de 9.357 filas y 13 columnas,
indexada por `DatetimeIndex` horario y ordenada cronológicamente.

**Decisiones de implementación:**

1. **Formato de lectura declarado explícitamente** (`delimiter=';'`,
   `decimal=','`), por venir el fichero en formato europeo.

2. **Formato de fecha declarado explícitamente** (`%d/%m/%Y %H.%M.%S`) en
   lugar de dejar que pandas lo infiera. Se comprobó que la inferencia
   automática interpreta las fechas como formato americano (mes/día): con
   este fichero el error se detecta al llegar al 13 de marzo, pero en un
   conjunto que solo cubriera los doce primeros días de cada mes la serie
   quedaría desordenada **sin lanzar ningún error**. En un problema de
   predicción temporal eso invalidaría todos los retardos calculados
   posteriormente.

   Se optó por declarar los puntos como separador horario dentro del propio
   formato (`%H.%M.%S`) en lugar de sustituirlos previamente por dos puntos.
   Evita modificar el dato de origen.

3. **Eliminación de artefactos por criterio explícito.** Las filas finales se
   eliminan con `subset=['Date', 'Time']` —es decir, "filas sin sello
   temporal"— y no con `how='any'`. Ambas opciones producen hoy el mismo
   resultado, pero la segunda eliminaría en silencio cualquier fila que tuviera
   un solo hueco, que no es la intención.

4. **Ruta construida con `pathlib` a partir de `__file__`.** Una ruta relativa
   solo funcionaría ejecutando desde la raíz del proyecto. Se verificó que la
   función carga correctamente tanto desde la raíz como desde otros
   directorios.

5. **La ruta es un parámetro con valor por defecto**, para poder inyectar
   ficheros de prueba en los tests sin alterar el comportamiento habitual.

**Alcance deliberadamente limitado:** la estación no limpia ni valida. Los
valores -200 se conservan intactos, porque la estación 2 (Validate) necesita
poder contarlos e informar sobre ellos antes de que se conviertan en huecos en
la estación 3 (Clean).

**Hallazgo confirmado:** el rango real de los datos es del 10/03/2004 al
04/04/2005. La documentación oficial del dataset indica "marzo de 2004 a
febrero de 2005", por lo que hay casi dos meses de datos que la descripción del
origen no menciona. Trasladar a la memoria.

**Verificación adicional:** el rango temporal contiene exactamente 9.357 horas
y la tabla tiene exactamente 9.357 filas, sin duplicados. La serie está
completa, sin saltos horarios.

---

## 2026-07-29 — Nomenclatura de las estaciones

**Decisión:** los nombres de las estaciones en la documentación se alinean con
los de sus módulos de código: Load, Validate, Clean, EDA, Features, Split,
Model, Explain, Uncertainty, Serve, Monitor. Las estaciones 12 (Memoria) y 13
(Entrega) conservan nombre en español por no tener módulo asociado.

**Motivo:** tener dos vocabularios en paralelo —"estación de ingesta" frente a
`load.py`— obliga al lector a traducir constantemente y facilita las
incoherencias a medida que el proyecto crece.

**Consecuencia:** se actualizan las referencias existentes en `README.md` y en
las entradas anteriores de este diario. La convención general se mantiene:
identificadores de código en inglés, redacción en español.

## 2026-07-29 — Pruebas de la estación 1 (Load)

**Resultado:** `tests/test_load.py` con cuatro pruebas: dimensiones, tipo de
índice, orden y unicidad del índice, y desaparición de las columnas Date y
Time.

**Descartadas dos pruebas adicionales:**

- *Ausencia de saltos horarios.* Redundante: si el número de filas y el rango
  temporal son correctos, la continuidad de la serie se deduce por aritmética.

- *Verificación del formato europeo de fecha* (comprobar los valores concretos
  de fecha mínima y máxima). Es la única prueba capaz de detectar una lectura
  de fechas invertida, ya que las cuatro restantes la superarían: `sort_index()`
  deja el índice ordenado tanto si las fechas son correctas como si no. Se
  descarta porque, con este fichero concreto, una interpretación errónea del
  formato lanzaría una excepción al llegar al día 13 de un mes, de modo que el
  fallo sería ruidoso y no silencioso. La prueba recuperaría su valor si el
  conjunto de datos cambiase por otro cuyos días no superasen el 12.

**Criterio general adoptado:** se prueban los fallos que pueden producirse sin
lanzar ningún error, no todo lo que el código hace.

## 2026-07-29 — Cotas de plausibilidad de la estación 2 (Validate)

**Decisión:** las cotas de rango se fijan por criterio de plausibilidad física
y no por los límites legales de calidad del aire.

**Motivo:** son dos conceptos distintos. El límite legal marca lo que no
debería superarse por salud pública; superarlo es un episodio de
contaminación, no un error de medición. La cota de plausibilidad marca lo que
sería imposible medir.

Aplicar los límites legales como cotas de validación haría que el data contract
rechazase el fichero: `NO2(GT)` supera los 200 µg/m³ del límite horario
europeo en 386 horas, y su máximo observado es 340. Detectar esas
superaciones es precisamente el objetivo del proyecto (estación 9,
Uncertainty), no un motivo para rechazar el dato de entrada.

**Criterio aplicado por tipo de variable:**

- *Meteorología*: límites físicos (humedad relativa entre 0 y 100 por
  definición; temperatura según extremos históricos en Italia).
- *Analizador de referencia*: valor holgado sobre el máximo observado, pero
  suficientemente por debajo de lo que produciría un error de lectura de un
  orden de magnitud.
- *Sensores MOX*: rango del hardware. Devuelven señal eléctrica en unidades
  arbitrarias, no concentraciones, por lo que ninguna normativa les aplica.

**Corrección respecto a una versión anterior:** las cotas iniciales eran
excesivamente holgadas (hasta un 740 % de margen sobre el máximo observado en
`CO(GT)`). Una cota que nunca puede saltar no es una comprobación. Se
ajustaron tras comparar con los rangos reales de cada columna.

**Verificación:** se simuló un error de lectura del separador decimal
(multiplicación por diez de todos los valores) y el data contract lo detecta en las
trece columnas. Con las cotas anteriores, varias columnas lo habrían superado
sin incidencias.

## 2026-07-29 — Estación 2 (Validate) completada

**Resultado:** `src/tfm_airquality/validate.py` con siete comprobaciones que
conforman el *data contract* del proyecto, más cinco pruebas en
`tests/test_validate.py`.

**Qué es un data contract:** la lista escrita de todo lo que se da por supuesto
sobre el fichero de entrada, verificada explícitamente antes de dejar pasar el
dato al resto del pipeline. Es una práctica reconocida en ingeniería de datos.

**Motivo de su existencia:** el error caro en un proyecto de datos no es el que
rompe el programa, sino el que no lo rompe. La lectura ingenua del CSV
devolvía una tabla de una sola columna sin lanzar ninguna excepción. Ninguna
herramienta de programación protege de eso; solo una comprobación explícita de
lo esperado.

**Comprobaciones bloqueantes** (detienen el pipeline): columnas esperadas,
tipos numéricos, índice temporal (tipo, orden, unicidad y continuidad horaria)
y rangos de plausibilidad.

**Comprobaciones informativas** (avisan sin detener): número de filas, recuento
del marcador -200 y cobertura de la variable objetivo.

**Criterio del reparto:** bloquea lo que hace imposible continuar o revela un
error de lectura. Avisa lo que puede variar legítimamente. El recuento de -200
es informativo porque la abundancia de ausentes es una característica del
dataset, no un defecto del fichero: su valor es documental.

**Diseño de la implementación:** ninguna comprobación lanza excepciones.
Todas devuelven un objeto `Check` con su resultado, y la decisión de detener el
pipeline se toma al final. Así un solo diagnóstico muestra todos los problemas
a la vez, en lugar de obligar a corregirlos de uno en uno.

**Verificación del contrato:** se comprobó que rechaza tres tipos de deterioro
—columna ausente, valor físicamente imposible y salto en la serie horaria— y
que un aviso informativo no lo tumba. Un validador que solo se ha visto pasar
no demuestra nada.

**Cifras obtenidas** (confirman lo anotado como pendiente el 24 de julio):

- `NMHC(GT)`: 90,2 % de valores ausentes. Confirma su descarte.
- `NO2(GT)`: 7.715 horas observadas, el 82,5 %. Cobertura holgada para modelar.
- Marcador -200: 16.701 celdas, el 13,7 % del total.

## 2026-07-30 — Umbral de interpolación: 2 horas

**Decisión:** solo se interpolan las rachas de valores ausentes cuya longitud
completa no supera las 2 horas.

**Cómo se eligió:** en lugar de fijarlo por intuición, se midió el error que
introduce la interpolación. Se tomaron tramos con dato observado, se taparon
artificialmente, se interpolaron y se comparó lo estimado con lo real, para
longitudes de hueco de 1 a 12 horas.

Error absoluto medio de la interpolación en `NO2(GT)`, en µg/m³:

| Hueco | 1 h | 2 h | 3 h | 5 h | 8 h | 12 h |
|---|---|---|---|---|---|---|
| MAE | 9,4 | 12,4 | 14,6 | 19,3 | 26,5 | 27,6 |

**Hallazgo:** el error crece de forma suave y continua. **No existe ningún
punto de ruptura** que sugiera un umbral natural, de modo que la elección es
una decisión de compromiso y no una obviedad. Una hipótesis inicial de 5 horas
—basada en que la señal de los sensores varía poco a corto plazo— quedó
debilitada por estos números.

**Argumento de la elección:**

1. Con umbral de 5 horas, el error de interpolación (19,3 µg/m³) sería
   comparable al error del propio modelo de referencia por persistencia a una
   hora vista. Se estaría inyectando en las variables de entrada un ruido del
   mismo orden de magnitud que la señal que el proyecto pretende predecir.
   Con umbral de 2 horas el error es de 12,4 µg/m³, netamente inferior.
2. El beneficio de ampliar el umbral es marginal: en las columnas de sensores
   se pasaría de recuperar 3 horas a recuperar 15, sobre un total de 9.357.
   El coste en error sería del 55 % a cambio de 12 horas de dato.

**Estructura real de los huecos, medida por columna:**

- `NO2(GT)` y `NOx(GT)`: distribución bimodal. Rachas de 1 y 2 horas, y
  después un salto directo a 12 horas o más, sin nada intermedio.
- `CO(GT)` y las columnas de la placa de sensores: distribución continua, con
  rachas de 3, 4, 5, 8, 9 y 10 horas. **No hay zona vacía**, por lo que el
  argumento de "el umbral cae en un tramo sin datos" solo es válido para la
  variable objetivo.

**Concentración de las pérdidas:** en `NO2(GT)`, 320 de las 344 rachas son de
una sola hora, pero 21 averías de 12 horas o más concentran 1.316 de las 1.642
horas perdidas. El 80 % del dato ausente proviene de una veintena de paradas
del equipo, no de ruido disperso.

**Indicio confirmado sobre el benceno (primero de los tres anotados el 24 de
julio):** nueve columnas presentan exactamente el mismo patrón de ausencias
—366 valores, 16 rachas, máxima de 76 horas e idéntica distribución de
longitudes—: los cinco sensores PT08, `T`, `RH`, `AH` y **`C6H6(GT)`**. Las
demás variables del analizador de referencia (`CO`, `NOx`, `NO2`) tienen
patrones propios y distintos. El benceno falla cuando falla la placa de
sensores, no cuando falla el analizador.

## 2026-07-30 — Los huecos de una hora son un ciclo de calibración

**Hallazgo:** los huecos de una sola hora no están distribuidos al azar en el
día. Se concentran de forma abrumadora en una hora fija:

| Columna | Rachas de 1 h | Hora dominante |
|---|---|---|
| `NO2(GT)` | 320 | 304 a las 03:00 |
| `NOx(GT)` | 321 | 304 a las 03:00 |
| `CO(GT)` | 145 | 131 a las 04:00 |

**Interpretación:** corresponde al ciclo de autocalibración del analizador de
referencia, que durante el proceso no mide. NO₂ y NOx caen simultáneamente a
las 03:00 y CO una hora después, lo que es coherente con canales distintos del
mismo equipo calibrándose en secuencia.

**Consecuencias:**

1. Refuerza la decisión de interpolar los huecos cortos. No se está rellenando
   un fallo errático, sino una interrupción programada y predecible.
2. La ausencia no es completamente aleatoria: se produce siempre a la hora de
   menor tráfico y menor concentración. Introduce un sesgo pequeño pero real
   en cualquier estadística horaria nocturna, que conviene declarar.

**Cómo se detectó:** al revisar la salida de `gap_runs` se observó que varias
rachas consecutivas de una hora tenían la misma hora del día (03:00) en días
sucesivos. La comprobación de la distribución horaria lo confirmó.

## 2026-07-29 — Descarte de columnas en la estación 3 (Clean)

**Decisión:** solo se descarta `NMHC(GT)`. `C6H6(GT)` se conserva por ahora.

**Motivo del descarte de NMHC:** 90,2 % de valores ausentes, concentrados en 6
rachas, una de ellas de 8.126 horas consecutivas. El sensor estuvo apagado
prácticamente todo el periodo, casi 340 días. No hay nada que modelar.

**Motivo de conservar C6H6:** de los tres indicios anotados el 24 de julio
sobre su posible carácter derivado, solo uno está verificado con código propio
(el patrón de ausencias idéntico al de la placa de sensores). Los otros dos
—la correlación con `PT08.S2` y el número de valores distintos— se comprobarán
en la estación 4 (EDA). Descartar una columna con un indicio de tres sería
precipitado, y afirmar en la memoria que está derivada del sensor sin haberlo
comprobado sería una afirmación débil.

**Consecuencia técnica pendiente:** la salida de Clean tiene 12 columnas de
datos frente a las 13 que exige `config.EXPECTED_COLUMNS`. No supone un
problema ahora porque Validate se ejecuta antes de Clean, pero habrá que
resolverlo si en el futuro se valida también la salida de la limpieza.

## 2026-07-30 — Estación 3 (Clean) completada

**Resultado:** `src/tfm_airquality/clean.py` con cinco funciones y seis pruebas
en `tests/test_clean.py`.

- `sentinel_to_nan`: convierte el marcador -200 en hueco real.
- `gap_runs`: localiza inicio, fin y longitud de cada racha de huecos.
- `gap_report`: resumen de huecos por columna.
- `interpolate_short_gaps`: interpolación selectiva.
- `add_quality_flags`: metadatos de calidad por fila.
- `clean`: orquesta las anteriores.

**Cifras resultantes:** 7.396 horas utilizables (con objetivo observado y todas
las entradas disponibles) de 9.357. Solo 24 celdas del conjunto completo
proceden de interpolación.

**Decisión: no se eliminan filas.** Las horas sin objetivo observado se
conservan y se marcan con el indicador booleano `objetivo_observado`, en lugar
de borrarse. Borrarlas rompería la continuidad horaria de la serie, que es
justamente lo que comprueba la estación 2: sobre una serie con agujeros, un
retardo de 24 posiciones no retrocede 24 horas reales. El filtrado se hace en
el momento de entrenar y evaluar.

**Decisión: el informe de huecos se calcula antes de interpolar**, para que
describa el estado real del dato de origen y no el resultado de las propias
intervenciones. Es el que se llevará a la memoria.

**Error corregido durante la implementación:** un primer intento interpolaba
cada racha corta recortando la serie a los límites del propio hueco. Ese trozo
contiene únicamente valores ausentes, de modo que la interpolación devolvía
NaN y no rellenaba nada, sin lanzar ningún error. La versión final interpola la
serie completa —así cada hueco tiene vecinos con los que estimarse— y solo
después copia los valores en las posiciones autorizadas por la máscara.

**Prueba más relevante:** `test_hueco_largo_queda_intacto`, que verifica que
una racha de diez horas no se toca en absoluto. Es la garantía frente al atajo
`df.interpolate(limit=2)`, que rellenaría las dos primeras horas de una parada
larga.

## 2026-07-30 — Correlación por horizonte: tres hallazgos

**1. La correlación oscila con periodo de 24 horas.** Para `PT08.S5(O3)`, cae
desde 0,708 en el instante actual hasta un mínimo de 0,068 en h+17, repunta a
0,411 en h+24, vuelve a caer hasta hacerse negativa hacia h+41 y repunta de
nuevo en h+48. Los máximos coinciden con múltiplos de 24 horas.

Interpretación: el ciclo diario domina la serie. A h+6 se compara una hora del
día con otra de fase distinta; a h+24 las fases vuelven a alinearse. Es la
confirmación cuantitativa del ciclo diario y **justifica los retardos de 24 y
168 horas** de la estación 5: no se incluyen por convención, sino porque la
correlación repunta ahí.

**2. El pasado del objetivo predice mejor que cualquier sensor.** La
autocorrelación del NO₂ a 24 horas es 0,71, frente al 0,41 de la mejor
variable externa (`PT08.S5`). Esto cuantifica la diferencia esperable entre
escenarios antes de entrenar ningún modelo: el escenario A puede explotar esa
autocorrelación y el B no. También explica por qué el baseline estacional
diario será un rival exigente.

**3. La meteorología se refuerza al alejar el horizonte.** La humedad absoluta
pasa de −0,335 en el instante actual a −0,427 en h+48, y la temperatura de
−0,186 a −0,237. Son las únicas variables cuya relación con el objetivo
aumenta con el horizonte. Coherente con que la meteorología no determina el
NO₂ hora a hora, pero sí la capacidad de dispersión atmosférica a escala de
días. Refuerza la limitación ya anotada de no disponer de predicción
meteorológica.

**Multicolinealidad detectada:** `C6H6`×`PT08.S2` = 0,98; `C6H6`×`CO(GT)` =
0,93; `CO(GT)`×`PT08.S2` = 0,92; `PT08.S1`×`PT08.S5` = 0,90. Los sensores
miden en buena parte lo mismo, algo esperable dadas sus sensibilidades
cruzadas. Tiene consecuencia directa en la estación 8: SHAP repartirá la
importancia de forma arbitraria entre variables casi intercambiables, y habrá
que declararlo al interpretar.

**Segundo indicio del benceno confirmado:** la correlación de 0,98 con
`PT08.S2`. Quedan dos de tres indicios verificados; falta el número de valores
distintos.

## 2026-08-10 — Autocorrelación del NO₂

**Medida hasta 192 horas (ocho días).**

| Retardo | 1 h | 6 h | 12 h | 24 h | 48 h | 168 h |
|---|---|---|---|---|---|---|
| Autocorrelación | 0,900 | 0,352 | 0,234 | 0,708 | 0,573 | 0,646 |

**Ciclo diario.** La autocorrelación cae hasta un mínimo de 0,234 en el retardo
de 12 horas —la fase opuesta del ciclo— y repunta a 0,708 en 24 horas. Es el
mismo fenómeno detectado en la correlación con los sensores, ahora medido
sobre la propia serie.

**Ciclo semanal aislado.** Siguiendo solo los múltiplos de 24 horas, la
autocorrelación desciende del día 1 (0,708) al día 4 (0,508) y después remonta
hasta 0,646 en el retardo de 168 horas, volviendo a caer en 192 (0,573). El
pico semanal destaca sobre sus vecinos, lo que confirma la estacionalidad
semanal ya observada en el perfil por día de la semana.

**Consecuencias:**

- *Estación 5 (Features):* se construirán retardos de 1, 24 y 168 horas. Los
  tres tienen justificación medida y no meramente convencional.
- *Estación 6 (Split):* los modelos de referencia serán persistencia (retardo
  1), estacional diario (24) y estacional semanal (168).

**Expectativa realista que conviene dejar anotada:** con una autocorrelación de
0,708 a 24 horas, el modelo de referencia estacional diario será un rival
exigente. Batirlo de forma consistente en los 48 horizontes es el reto central
del proyecto, y cabe la posibilidad de que la mejora resulte modesta. En ese
caso el resultado honesto es declararlo, no presentarlo como fracaso: cuantifica
cuánta señal aprovechable hay más allá de la inercia de la propia serie.

**Estructura de los episodios.** Las 386 superaciones se agrupan en 136
episodios, con una duración media de 2,8 horas y máxima de 18. El 35 % dura
una sola hora, pero el 42 % (57 episodios) se prolonga tres horas o más.

Los episodios no son picos aislados: hay un fenómeno sostenido que anticipar.
Es relevante para el caso de negocio, ya que una superación puntual de una
hora no justifica activar un protocolo de restricción de tráfico, mientras que
un episodio de ocho a dieciocho horas sí.

**Nota metodológica.** El cálculo se realiza sobre la serie de horas
observadas (`dropna()`), no sobre la serie completa. Reutilizar `gap_runs`
sobre la serie con huecos mezclaba los episodios de contaminación con las
paradas del analizador: las duraciones máximas resultantes (173, 146, 142
horas) coincidían exactamente con las rachas de datos ausentes ya
caracterizadas. La comprobación de que las horas de los episodios suman
exactamente 386 valida el resultado.

Efecto secundario asumido: al eliminar las horas ausentes, dos superaciones
separadas por un hueco quedan contiguas y se contabilizan como un único
episodio. Dado el objetivo del análisis —determinar si los episodios son
puntuales o sostenidos—, el efecto no altera la conclusión.

## 2026-08-10 — Deriva de la relación sensor-concentración

**Pregunta:** ¿se mantiene estable a lo largo del año la relación entre la
señal de los sensores y la concentración medida por el analizador?

**Método.** Dos indicadores por mes: la correlación entre cada sensor y el
objetivo, y el cociente entre la concentración media y la señal media. El
primero mide si el sensor sigue informando; el segundo, si el factor de
conversión se desplaza.

**Resultado 1: la correlación mensual se mantiene.** Los cinco sensores
conservan correlaciones altas dentro de cada mes durante todo el periodo. Los
sensores no pierden capacidad de informar.

**Resultado 2: el factor de conversión se desplaza.** Comparando el mismo mes
de años consecutivos (marzo de 2004 frente a marzo de 2005), que comparten
régimen estacional:

| Sensor | Mar 2004 | Mar 2005 | Cambio |
|---|---|---|---|
| PT08.S1 | 83,9 | 119,7 | +43 % |
| PT08.S2 | 109,6 | 154,3 | +41 % |
| PT08.S3 | 99,7 | 193,3 | +94 % |
| PT08.S4 | 65,3 | 111,9 | +71 % |
| PT08.S5 | 99,8 | 126,4 | +27 % |

Para una misma señal del sensor, la concentración real asociada es entre un
27 % y un 94 % mayor un año después.

**Hipótesis alternativas consideradas:**

- *Efecto estacional.* Descartada: la comparación se hace entre el mismo mes
  de años consecutivos, con idéntico régimen estacional.
- *Aumento del tráfico urbano.* Descartada por dos motivos. Primero, un año
  es un plazo demasiado corto para un cambio del 40 % en el parque
  automovilístico. Segundo, y decisivo, un aumento de emisiones elevaría a la
  vez la concentración real y la señal del sensor, dejando el cociente
  estable; que el cociente se desplace indica que ambas magnitudes se han
  desacoplado.

**Hipótesis que NO pueden descartarse con este diseño experimental:** deriva
del propio analizador de referencia (no se dispone de un tercer instrumento
que arbitre), cambios en el entorno inmediato de medida, o mantenimiento de
los equipos durante el periodo. La memoria debe declarar esta limitación en
lugar de atribuir el desplazamiento exclusivamente a los sensores.

**Por qué la causa exacta no altera la conclusión operativa:** sea cual sea el
origen, el hecho medido es que un modelo calibrado con datos de un año está
sistemáticamente desviado doce meses después, y lo está sin emitir ningún
aviso. Esto justifica de forma cuantitativa —y no meramente por buena
práctica— las estaciones 9 (intervalos que se ensanchan al desplazarse la
relación) y 11 (monitorización y política de reentrenamiento).

**Hallazgo adicional: paradoja de Simpson en PT08.S4.** El sensor nominalmente
dedicado al NO₂ presenta una correlación global de solo 0,16 con el objetivo,
pero correlaciones mensuales altas (0,835 en marzo de 2004, 0,801 en octubre).
Dentro de cada mes sigue bien al NO₂; entre meses, su nivel base se desplaza
lo suficiente (+71 % en un año, el mayor de los cinco) como para destruir la
relación global. Es un ejemplo de manual de agregación engañosa y merece
figura propia en la memoria.

## 2026-08-10 — Estación 5: elección de retardos y codificación cíclica

**Retardos elegidos: 1, 24 y 168 horas.** Son los tres máximos locales de la
curva de autocorrelación medida el 10 de agosto: 0,900 (inercia inmediata),
0,708 (misma hora del día anterior) y 0,646 (misma hora del mismo día de la
semana anterior). No responden a convención sino a los puntos donde la serie
conserva más información sobre sí misma.

Se descartan retardos intermedios: el de 12 horas tiene autocorrelación de
0,234 por corresponder a la fase opuesta del ciclo diario, y el de 96 horas
(0,508) no destaca sobre sus vecinos. El de 168 sí destaca frente a 144
(0,583) y 192 (0,573), lo que confirma que la estacionalidad semanal es real y
no un artefacto.

**Codificación cíclica de las variables de calendario.** La hora del día se
representa mediante el seno y el coseno del ángulo correspondiente
(2π·hora/24) en lugar de como un entero de 0 a 23. Igual tratamiento para el
día de la semana (periodo 7) y el mes (periodo 12).

*Motivo:* en la representación entera, las 23:00 y las 00:00 quedan en
extremos opuestos de la escala pese a ser consecutivas, lo que introduce una
discontinuidad artificial cada medianoche. La codificación cíclica sitúa cada
hora como un punto de una circunferencia: la hora 0 da (sen 0, cos 1) y la
hora 23 da (−0,26, 0,97), es decir, prácticamente el mismo punto.

*Alcance real de la mejora:* los modelos basados en árboles no la necesitan,
ya que pueden establecer particiones en cualquier punto del rango. Sí importa
para los modelos lineales de la escalera de modelización, donde una recta
sobre la hora impondría un efecto monótono, incompatible con el perfil horario
observado (mínimo a las 04:00, pico a las 10:00, valle a las 14:00 y máximo a
las 19:00). Se incluye para que la comparación entre modelos de la estación 7
sea equitativa.

## 2026-08-10 — Estación 5 (Features) completada

**Resultado:** `src/tfm_airquality/features.py` con cuatro funciones y cuatro
pruebas en `tests/test_features.py`.

- `add_lags`: retardos de 1 y 24 horas.
- `add_rolling`: medias y desviaciones de ventanas de 3 y 24 horas.
- `add_calendar`: hora, día de la semana y mes con codificación cíclica, más
  indicador de fin de semana.
- `build_features`: ensambla las anteriores y desplaza el objetivo.

**Decisión: un único modelo para los 48 horizontes**, con el horizonte como
variable de entrada, frente a la alternativa de entrenar 48 modelos
independientes. Un modelo global generaliza mejor con un volumen de datos
limitado y resulta mucho más barato de mantener en producción. La tabla
resultante contiene una fila por cada combinación de instante y horizonte:
449.136 filas y 287 MB, volumen manejable sin necesidad de procesamiento por
bloques.

**Ventanas móviles de 3 y 24 horas.** La de 24 captura un ciclo diario
completo, cuya relevancia está medida (autocorrelación de 0,708 a ese
retardo). La de 3 horas se apoya en que la autocorrelación a ese plazo sigue
siendo alta (0,612), mientras que a 6 horas ya desciende a 0,352. Se emplea
`min_periods` igual a la mitad de la ventana: con el comportamiento estricto
por defecto, un solo valor ausente anularía la ventana completa, y con 1.642
horas ausentes en el objetivo eso descartaría una parte considerable del
conjunto.

**Pérdida de filas por propagación de huecos.** Al construir las variables, las
filas completas descienden de 7.396 a 5.104, un 31 % menos. La causa es que
cada hora ausente inutiliza además la fila siguiente en el retardo de 1 hora,
la de 24 horas después en el de 24, y la de una semana después en el de 168.

**Distribución mensual desigual.** Las filas útiles no se reparten de forma
homogénea: octubre de 2004 conserva 103 de sus 744 horas (14 %), frente a
marzo de 2005 con 695 (93 %). Los meses más mermados coinciden con las averías
prolongadas del analizador ya caracterizadas (173 y 142 horas consecutivas, en
octubre ambas).

**Decisión aplazada sobre el retardo de 168 horas.** Prescindir de él elevaría
las filas completas de 5.104 a 6.217 (+22 %) y triplicaría las de octubre (de
103 a 314). A cambio se perdería la señal semanal, cuya existencia está medida
(autocorrelación de 0,646, destacando sobre 144 y 192).

No se decide ahora: la columna se construye —siempre puede ignorarse una
variable existente, pero no usarse una que no se ha creado— y ambas
configuraciones se compararán empíricamente en la estación 7 con el mismo
arnés de evaluación, del mismo modo que se procedió con el umbral de
interpolación.

**Prueba más relevante: `test_sin_fuga_de_informacion`.** Altera todos los
valores posteriores a un instante dado y verifica que las variables
construidas en ese instante no cambian. Es el guardián de la regla central de
la estación: toda columna debe poder calcularse empleando exclusivamente
información anterior o igual al instante actual. Una variable que mire al
futuro —una media móvil centrada, un desplazamiento de signo invertido—
produciría métricas excelentes en evaluación y un fallo completo en
producción, sin lanzar ningún error.

## 2026-08-21 — Embargo entre entrenamiento y evaluación

**Decisión:** se descartan las 48 horas previas a la fecha de corte, que no se
emplean ni para entrenar ni para evaluar.

**Motivo:** sin embargo, la última fila de entrenamiento (31/12/2004 a las
23:00) tendría, para el horizonte de 24 horas, su valor objetivo situado el 1
de enero de 2005, es decir, dentro del periodo de evaluación. El modelo
aprendería durante el entrenamiento cómo empieza el tramo con el que después
se le va a puntuar.

No es una fuga de información en sentido estricto —ninguna variable de entrada
procede del futuro—, pero sí un solapamiento entre ambos conjuntos que conviene
eliminar.

**Dimensionado:** el embargo debe igualar al horizonte máximo de predicción, 48
horas en este proyecto. Con un embargo menor, las filas correspondientes a los
horizontes más largos seguirían solapando.

**Coste:** 48 filas de entrenamiento sobre 7.110, un 0,7 %. El conjunto de
entrenamiento pasa a terminar el 29/12/2004 a las 23:00.

**Nombre de la técnica:** se conoce como *embargo* o *purga* y es práctica
habitual en la validación de modelos sobre series temporales, donde los
conjuntos de entrenamiento y evaluación pueden solaparse a través de la
variable objetivo aunque las entradas estén correctamente separadas.

## 2026-08-21 — Estación 6 (Split) completada

**Resultado:** cuatro módulos —`split.py`, `metrics.py`, `baselines.py` y
`evaluate.py`— y cuatro pruebas en `tests/test_split.py`.

**Métricas.** MAE y RMSE se toman de scikit-learn; solo se implementa el
tratamiento de ausentes (las funciones de la librería no admiten NaN y hay
1.642 horas sin valor real, que no pueden puntuarse ni rellenarse) y el skill
score, que no está disponible en la librería.

**Modelos de referencia.** Persistencia, estacional diario y estacional
semanal, correspondientes a los tres máximos de la curva de autocorrelación.
Todos emplean exclusivamente información anterior o igual al instante actual.
En el estacional diario, los horizontes superiores a 24 horas retroceden dos
días en lugar de uno: con un solo día, el instante de referencia caería en el
futuro.

**Resultados del listón (periodo de test, enero-abril de 2005):**

| Horizonte | Mejor baseline | MAE (µg/m³) |
|---|---|---|
| 1 h | Persistencia | 18,66 |
| 6 h | Estacional diario | 32,93 |
| 24 h | Persistencia / diario (idénticos) | 32,93 |
| 48 h | Estacional semanal | 39,24 |

**MAE medio del listón sobre los 48 horizontes: 35,68 µg/m³.** Es la cifra de
referencia del proyecto: a partir de la estación 7, todo modelo se juzga por
si consigue rebajarla. Para dimensionarla, la media del NO₂ en el conjunto es
de 113 µg/m³, de modo que el método de referencia se equivoca en torno a un
32 % del valor típico.

**Reparto de victorias:** el estacional semanal es el mejor en 23 horizontes,
el diario en 21 y la persistencia solo en 4, los más cortos. No existe un
único baseline que domine, lo que justifica exigir que el modelo supere al
mejor de los tres en cada horizonte y no a uno cualquiera.

**Hallazgo: el error de la persistencia no crece de forma monótona.** A 6
horas comete un MAE de 53,57, muy superior al de 24 horas (32,93). Es
consecuencia del ciclo diario: a 6 horas vista se compara una hora del día con
otra de fase opuesta, mientras que a 24 horas las fases se alinean. Es el
mismo fenómeno que la oscilación de la correlación detectada el 30 de julio,
ahora traducido a error de predicción.

**Comportamiento esperado que conviene documentar:** el estacional diario
produce un MAE idéntico para h=1, h=6 y h=24, y en h=24 coincide exactamente
con la persistencia. No es un error: los tres casos acaban comparando el mismo
par de instantes separados por 24 horas, y para h=24 el desplazamiento es
cero, es decir, el método es literalmente la persistencia.

**Prueba más relevante: `test_baselines_no_miran_al_futuro`.** Altera todos los
valores posteriores a un instante y verifica que la predicción en ese instante
no cambia, para los tres baselines y tres horizontes distintos. Es el
equivalente al test de fuga de la estación 5.

## 2026-08-21 — Estación 7: selección de la escalera de modelos

**Criterio general.** Los modelos no se eligen por variedad, sino porque cada
uno responde a una pregunta concreta y permite descartar una hipótesis. Se
asciende por la escalera de uno en uno y solo se justifica un nivel superior
si mejora al anterior: un modelo complejo que no supera a uno simple se
descarta, con independencia de su sofisticación.

---

**Nivel 1 — Ridge.** *¿Basta con una relación lineal?*

Es la referencia interpretable del proyecto: sus coeficientes se leen
directamente. Se emplea la variante regularizada y no una regresión lineal
ordinaria porque el conjunto presenta multicolinealidad severa, medida en la
estación 4: `PT08.S1` y `PT08.S5` correlacionan 0,90, y las medias móviles
correlacionan fuertemente con sus propios retardos. Sin regularización, los
coeficientes serían inestables y no interpretables.

**Nivel 2 — Random Forest.** *¿Existen relaciones no lineales?*

Primer modelo no lineal. Robusto, con pocos hiperparámetros críticos y
tolerante a la multicolinealidad. Su función es principalmente diagnóstica: si
mejora sustancialmente a Ridge, la no linealidad es relevante; si no, el
problema es esencialmente lineal y conviene saberlo antes de invertir en
modelos más complejos.

**Nivel 3 — LightGBM.** *¿Cuánto puede exprimirse el enfoque tabular?*

Gradient boosting sobre árboles, estándar de facto en problemas tabulares. Dos
ventajas específicas para este conjunto: admite valores ausentes de forma
nativa —lo que es determinante cuando solo 5.104 de las 449.136 filas están
completas— y captura interacciones entre variables, como que el efecto de la
temperatura sobre el NO₂ difiera según la estación del año.

**Nivel 4 — XGBoost.** *¿Depende el resultado de la implementación concreta?*

No aporta un enfoque metodológico nuevo: es otra implementación de gradient
boosting. Se incluye como control de robustez. Si LightGBM y XGBoost arrojan
resultados muy dispares, es señal de sobreajuste o de sensibilidad excesiva a
los hiperparámetros; si convergen, aumenta la confianza en la cifra obtenida.

**Nivel 5 — SARIMAX.** *¿Aporta algo el enfoque estadístico clásico?*

Cambia de paradigma respecto a los cuatro anteriores. Estos tratan el problema
como tabular, tras haber convertido la historia en columnas durante la
estación 5; SARIMAX lo aborda como serie temporal pura, modelando de forma
explícita la autocorrelación y la estacionalidad.

*Limitación reconocida:* no encaja de manera natural con el diseño de modelo
global con el horizonte como variable de entrada. Requerirá adaptación o
evaluación separada, y puede acabar funcionando más como ejercicio comparativo
que como candidato real al modelo final.

**Nivel 6 — Perceptrón multicapa (MLP).** *¿Aporta algo una red neuronal?*

Alternativa no lineal de familia distinta a los árboles: aproxima funciones
suaves, mientras que los modelos basados en árboles aproximan por escalones.
Con el volumen de datos disponible es poco probable que resulte competitivo
—las redes neuronales requieren conjuntos mayores—, pero se prefiere
descartarlo con evidencia antes que por intuición.

---

**Modelos descartados y motivo:**

| Modelo | Motivo del descarte |
|---|---|
| SVR | Escala mal con cientos de miles de observaciones |
| KNN | Mismo problema de escalado; además sufre la maldición de la dimensionalidad con 80 variables |
| Prophet | Concebido para series con estacionalidad marcada y pocos regresores externos; no aprovecharía las variables construidas |
| LSTM, N-BEATS, TFT | Descartados por restricción de calendario el 29 de julio; requieren mayor volumen de datos y más tiempo de desarrollo del disponible |

---

**Procedimiento de comparación acordado:**

1. Ronda inicial con hiperparámetros por defecto sobre un subconjunto de
   horizontes, para descartar rápidamente los modelos no competitivos.
2. Búsqueda de hiperparámetros mediante `GridSearchCV` únicamente sobre el
   ganador o los dos mejores.
3. Evaluación final sobre los 48 horizontes.

*Motivo del orden:* una búsqueda exhaustiva sobre seis modelos supondría
cientos de entrenamientos sobre 449.136 filas. La ronda inicial con valores
por defecto indica en minutos si algún modelo se aproxima siquiera al listón
de 35,68 µg/m³; si ninguno lo hiciera, el ajuste de hiperparámetros no
resolvería el problema.

**Requisito metodológico de la validación cruzada:** debe emplearse
`TimeSeriesSplit` y no la validación cruzada por defecto de scikit-learn, que
reparte las observaciones al azar. Sobre una serie temporal, un reparto
aleatorio permitiría entrenar con datos posteriores a los de validación, lo
que produciría métricas excelentes y carentes de validez.

## 2026-08-21 — Corrección: afirmaciones sobre el coste de los equipos

**Problema detectado.** La entrada del 24 de julio sobre los dos escenarios de
despliegue, y el planteamiento del problema en el README, afirmaban que los
sensores de óxido metálico son "de bajo coste" frente a un "equipo caro", y el
README llegaba a cuantificarlo ("decenas de miles de euros", "dos órdenes de
magnitud menos").

**Ninguna de esas afirmaciones está sostenida por el conjunto de datos.** La
documentación del origen describe la tecnología de los dispositivos —sensores
de óxido metálico frente a un analizador certificado— pero no menciona precios
en ningún momento. Se trataba de contexto asumido, no de un dato verificado.

**Corrección aplicada.** El README se reformula para describir la diferencia
entre ambas tecnologías sin afirmar nada sobre su precio: los métodos de
referencia (quimioluminiscencia para el NO₂) requieren infraestructura,
mantenimiento y calibración periódica, mientras que los dispositivos
multisensor permitirían desplegar un mayor número de puntos de medida. El
título del trabajo pasa de "con sensores de bajo coste" a "a partir de
sensores de óxido metálico".

**La pregunta del proyecto no cambia**, porque no dependía del precio: ¿puede
un nodo equipado únicamente con sensores de óxido metálico aproximar las
mediciones de un analizador certificado situado en el mismo punto? Eso es
verificable con los datos disponibles.

**Vía para recuperar el argumento económico:** si se desea mantenerlo en la
memoria, debe apoyarse en una referencia bibliográfica. El artículo de De Vito
et al. (2008), de cita obligatoria, contextualiza el uso de sensores químicos
en despliegues de campo, y existe literatura abundante sobre redes de sensores
de bajo coste para calidad del aire. Sin cita, la afirmación se omite.

**Lección metodológica:** conviene revisar periódicamente qué afirmaciones del
proyecto proceden de los datos y cuáles de supuestos incorporados sin
verificar. Es el mismo criterio aplicado a los indicios sobre `C6H6(GT)`, que
no se dieron por buenos hasta comprobarlos con código propio.

## 2026-08-21 — Descarte de SARIMAX

**Decisión:** SARIMAX se retira de la escalera de modelos. Se documenta como
alternativa considerada, sin implementación.

**Motivo principal, de diseño.** En la estación 5 el problema se transformó
deliberadamente de serie temporal a tabular, incorporando la historia como
columnas (retardos, ventanas móviles y calendario). Esa transformación es la
que permite emplear cualquier modelo tabular y mantener un único modelo para
los 48 horizontes.

SARIMAX exige deshacer esa transformación: modela la secuencia directamente y
no aprovecha las variables construidas. Evaluarlo obligaría a montar un
procedimiento distinto al del resto, lo que impediría una comparación en
igualdad de condiciones.

**Limitación adicional.** SARIMAX admite un único periodo estacional, mientras
que la serie presenta dos con relevancia medida: diario (autocorrelación 0,708
a 24 horas) y semanal (0,646 a 168). Habría que renunciar a uno de los dos.

**Coste de una evaluación rigurosa.** El procedimiento correcto sería de origen
móvil: ajustar el modelo con todo lo anterior a cada instante del test y
proyectar 48 horas. Sobre las 2.247 horas del periodo de evaluación, y con el
coste de ajustar un modelo estacional de periodo 24 sobre miles de
observaciones, no resulta asumible dentro del calendario del trabajo. Una
evaluación sobre una muestra de orígenes sería viable, pero produciría
resultados menos comparables con los de los demás modelos.

**Alternativas ya cubiertas.** La escalera conserva cinco modelos que sí
comparten procedimiento de evaluación y cubren tres familias distintas:
lineal regularizado (Ridge), ensambles de árboles por bagging (Random Forest)
y por boosting (LightGBM y XGBoost), y redes neuronales (MLP).

**Valor de dejarlo documentado:** descartar una alternativa con criterio
explícito es en sí una decisión de ingeniería. En la memoria se menciona como
opción evaluada y no seleccionada, indicando el motivo.

## 2026-08-22 — El escenario B pasa a ser análisis complementario

**Decisión:** el escenario A (con acceso al histórico del analizador de
referencia) es el trabajo principal. El escenario B queda documentado como
análisis complementario en la memoria, sin desarrollarse en las estaciones
posteriores.

**Motivo:** el objetivo del proyecto, fijado el 24 de julio, es la predicción
de NO₂ a 24-48 horas. Ese objetivo tiene sentido tanto en un emplazamiento con
analizador como sin él: el analizador mide el presente, no el futuro. El
escenario A es el caso principal y el que ofrece mejores resultados.

**Resultados obtenidos del escenario B** (LightGBM ajustado, mismos
hiperparámetros que el escenario A):

| Horizonte | Escenario A | Escenario B | Pérdida |
|---|---|---|---|
| 1 h | 18,12 | 30,86 | +70 % |
| 6 h | 29,96 | 33,87 | +13 % |
| 12 h | 30,30 | 33,38 | +10 % |
| 24 h | 31,21 | 35,70 | +14 % |
| 48 h | 32,36 | 36,27 | +12 % |
| Media | 28,39 | 34,02 | +20 % |

**Interpretación:** prescindir del histórico del analizador cuesta entre un
10 % y un 14 % de precisión en los horizontes operativamente relevantes. La
pérdida se dispara en el horizonte de una hora (+70 %), donde disponer de la
medición actual equivale casi a conocer la respuesta —la autocorrelación a una
hora es de 0,900—, pero ese horizonte carece de utilidad para anticipar
episodios.

**Resultado destacable:** a 48 horas el escenario B obtiene un MAE de 36,27
frente a los 39,24 del mejor modelo de referencia, pese a que estos sí emplean
el histórico certificado del que el escenario B no dispone.

**Limitación del análisis:** el escenario B se evaluó con los hiperparámetros
optimizados para el escenario A. Un ajuste específico podría mejorar
ligeramente sus cifras. No se realiza por restricción de calendario, y se
declara en la memoria.

## 2026-08-22 — Se elimina el retardo de 168 horas

**Decisión:** el retardo de 168 horas se retira del conjunto de variables. Se
resuelve así la decisión aplazada el 10 de agosto.

**Resultado de la comparación empírica** (LightGBM ajustado, escenario A,
mismos hiperparámetros en ambos casos):

| Horizonte | Con lag168 | Sin lag168 | Diferencia |
|---|---|---|---|
| 1 h | 18,12 | 17,74 | −0,38 |
| 6 h | 29,96 | 29,71 | −0,25 |
| 12 h | 30,30 | 30,30 | 0,00 |
| 24 h | 31,21 | 30,09 | −1,12 |
| 48 h | 32,36 | 31,28 | −1,08 |
| Media | 28,39 | 27,83 | **−0,56** |

Mejora en cuatro de los cinco horizontes y empate en el quinto. La mejora es
mayor precisamente en los horizontes largos, que son los relevantes para el
caso de uso.

**Por qué una variable con señal medida empeora el modelo.** La autocorrelación
a 168 horas es de 0,646, la tercera más alta de la serie y destacando sobre sus
vecinas (0,583 en 144 y 0,573 en 192). La señal semanal existe. Pero construir
la variable cuesta 1.113 filas de entrenamiento —de 6.217 a 5.104, un 18 %—,
porque cada hora ausente inutiliza además la fila situada una semana después.
El balance entre información aportada y observaciones perdidas resulta
negativo.

**Aclaración:** se elimina el retardo de 168 horas como variable predictora, no
el modelo de referencia estacional semanal, que se mantiene en `baselines.py`
y es el mejor baseline en 23 de los 48 horizontes. El baseline no construye
tabla de variables y por tanto no incurre en la pérdida de observaciones que
motiva esta decisión.

## 2026-08-22 — Descartada la especialización por tramos de horizonte

**Hipótesis:** dado que los horizontes cortos y largos mostraban
comportamientos distintos ante cambios de capacidad del modelo, dos modelos
especializados podrían superar a uno global.

**Resultado:** MAE medio de 27,88 con dos modelos (corte en h=12) frente a
27,83 con el modelo global. Diferencia de 0,05 µg/m³, dentro del ruido de una
única partición de test. Sin patrón claro por horizonte: mejora en h=6 y h=48,
empeora en h=1 y h=12.

**Interpretación.** Al incluir el horizonte como variable de entrada, el modelo
global ya puede especializarse internamente: un árbol puede establecer una
partición en `horizonte <= 12` y aplicar reglas distintas a cada lado. La
división manual reproduce a mano lo que el modelo hace por sí solo, y añade el
inconveniente de que cada submodelo entrena con la mitad de observaciones.

**Consecuencia:** se mantiene el modelo global único. La decisión adoptada en
la estación 5 —un solo modelo con el horizonte como variable, frente a 48
modelos independientes— queda validada empíricamente y no solo por argumentos
de coste de mantenimiento en producción.

## 2026-08-22 — Estación 7 (Model): alcance final y modelo seleccionado

**Decisión sobre el alcance de horizontes.** El pipeline se limita a cinco
horizontes operativos: 1, 6, 12, 24 y 48 horas. Se fijan en
`config.HORIZONTES` y son el valor por defecto de `build_features`.

*Motivo:* corresponden a decisiones reales —reacción inmediata, mismo día,
mañana y pasado mañana—. Un horizonte intermedio como 34 horas no se
corresponde con ninguna decisión que se tome en la práctica. Además, con cinco
horizontes cada uno representa el 20 % del conjunto y el modelo global único
funciona correctamente, sin necesidad de especialización por tramos, lo que
simplifica sustancialmente las estaciones 10 (Serve) y 11 (Monitor): un solo
modelo que desplegar, versionar y monitorizar en lugar de cuatro.

*Coste asumido:* el sistema no predice horizontes distintos de los cinco
fijados. Se declara como limitación.

**Modelo seleccionado:** LightGBM con `n_estimators=500`, `num_leaves=63` y
`learning_rate=0.05`, escenario A, sin el retardo de 168 horas.

**Resultados sobre los cinco horizontes operativos:**

| Horizonte | Listón | Modelo | Mejora |
|---|---|---|---|
| 1 h | 18,66 | 17,74 | 4,9 % |
| 6 h | 32,93 | 29,71 | 9,8 % |
| 12 h | 32,93 | 30,30 | 8,0 % |
| 24 h | 32,93 | 30,09 | 8,6 % |
| 48 h | 39,24 | 31,28 | 20,3 % |
| **Media** | **31,34** | **27,83** | **11,2 %** |

**Análisis complementario para la memoria.** Se conserva la evaluación sobre
los 48 horizontes con especialización por tramos, que no forma parte del
sistema desplegado pero aporta la curva de degradación del error frente al
horizonte de predicción. Sobre ese conjunto, el modelo supera al mejor
baseline en 36 de los 48 horizontes, con un skill medio del 7,7 %. Las mayores
ganancias se concentran entre 2 y 5 horas (hasta el 29 %) y existe una banda
entre 15 y 22 horas donde el estacional diario resulta ligeramente superior,
siempre por debajo del 5 %.

Los resultados se guardan en `reports/degradacion_48h.csv` y la figura
correspondiente en `reports/figuras/degradacion_por_horizonte.png`.

## Plantilla para nuevas entradas

    ## AAAA-MM-DD — Título breve

    **Decisión:** qué se ha decidido.

    **Motivo:** por qué, con datos concretos si los hay.

    **Alternativas descartadas:** qué más se valoró y por qué no.

    **Consecuencia:** qué implica para el resto del trabajo.