FROM python:3.12-slim

WORKDIR /app

# Se copian primero las dependencias para aprovechar la cache de capas: si el
# codigo cambia pero pyproject.toml no, no se reinstala todo.
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

# El modelo entrenado viaja con la imagen.
COPY models/ ./models/

EXPOSE 8000

# --host 0.0.0.0 es imprescindible: por defecto uvicorn solo escucha en
# 127.0.0.1, que dentro del contenedor significa "solo yo".
CMD ["uvicorn", "tfm_airquality.api:app", "--host", "0.0.0.0", "--port", "8000"]