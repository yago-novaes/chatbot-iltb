# --- Build stage ---
FROM python:3.11-slim AS builder

WORKDIR /build
COPY app/requirements.txt .

# Instala dependências em venv isolado
RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# Pre-download do modelo de embedding para cache fixo
ENV HF_HOME=/model_cache
RUN /venv/bin/python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# --- Runtime stage ---
FROM python:3.11-slim

WORKDIR /app

# Copia venv completo e modelo do builder
COPY --from=builder /venv /venv
COPY --from=builder /model_cache /root/.cache/huggingface

# Copia código e documentos
COPY app/ ./app/
COPY docs/protocolos/ ./docs/protocolos/

ENV PYTHONUNBUFFERED=1
ENV PATH="/venv/bin:$PATH"
ENV HF_HOME=/root/.cache/huggingface

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
