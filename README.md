# TFM — Predicción de NO2 con sensores de bajo coste

Trabajo Fin de Máster (UCM). Predicción de NO2(GT) a horizontes de 1 a 48
horas, usando el dataset Air Quality del UCI Machine Learning Repository.

## Instalación

Los datos no están en este repositorio. Descarga `AirQuality.csv` y
colócalo en `data/raw/`.

## Estructura

    src/tfm_airquality/   código del pipeline, estación a estación
    tests/                pruebas del código
    docs/                 diario de decisiones y notas
    data/                 datos (ignorado por git)

## Estado

- [ ] Estación 1 — Ingesta
- [ ] Estación 2 — Validación
- [ ] Estación 3 — Limpieza