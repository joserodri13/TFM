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

## 2026-07-29 — Umbral de interpolación: 2 horas

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

## Plantilla para nuevas entradas

    ## AAAA-MM-DD — Título breve

    **Decisión:** qué se ha decidido.

    **Motivo:** por qué, con datos concretos si los hay.

    **Alternativas descartadas:** qué más se valoró y por qué no.

    **Consecuencia:** qué implica para el resto del trabajo.