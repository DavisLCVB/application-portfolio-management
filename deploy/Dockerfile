FROM python:3.12-slim

WORKDIR /app

# El MVP solo usa la biblioteca estándar; se copia completo.
COPY mvp/ ./mvp/

# La API FastAPI y sus dependencias.
COPY deploy/requirements.txt ./deploy/requirements.txt
COPY deploy/app.py ./deploy/app.py
RUN pip install --no-cache-dir -r deploy/requirements.txt

ENV PORT=8080
EXPOSE 8080

# Cloud Run exige escuchar en 0.0.0.0:$PORT.
CMD ["uvicorn", "deploy.app:app", "--host", "0.0.0.0", "--port", "8080"]
