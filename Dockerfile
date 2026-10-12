# Dockerfile - reused from Week 6/8's pattern: a thin Python image running
# the triage API under uvicorn. No secret is ever baked into a layer --
# JWT_SECRET arrives at `docker compose up` time via env_file/environment
# (see docker-compose.yml), and app/auth.py fails closed at import time
# if it is missing (Deliverable 1).
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
