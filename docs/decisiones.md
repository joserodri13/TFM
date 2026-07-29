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
de umbrales se confirmarán con el código propio en la estación 4.

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

**Estado:** PENDIENTE DE VERIFICAR en la estación 4.

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
código (memoria y vídeo).

**Motivo:** una versión anterior agrupaba varias fases y dejaba fuera del
pipeline el análisis descriptivo, la interpretabilidad y los entregables
finales. Al no estar en la lista, corrían el riesgo de quedar relegados al
final. Con 13 estaciones, nada queda huérfano.

**Correspondencia con la guía:** fase i → estación 4; fase ii → estaciones 3 y
5; fase iii → estación 7; fase iv → estación 8; fase v → estación 12;
fase vi → estaciones 10 y 11.

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

**No negociable:** interpretabilidad (estación 8) y monitorización
(estación 11), por ser exactamente las fases que los tutores señalaron como
ausentes en las propuestas.

---

## Plantilla para nuevas entradas

    ## AAAA-MM-DD — Título breve

    **Decisión:** qué se ha decidido.

    **Motivo:** por qué, con datos concretos si los hay.

    **Alternativas descartadas:** qué más se valoró y por qué no.

    **Consecuencia:** qué implica para el resto del trabajo.