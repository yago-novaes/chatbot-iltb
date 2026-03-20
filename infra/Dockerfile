# --- Build stage ---
FROM python:3.11-slim AS builder

WORKDIR /build
COPY app/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Pre-download embedding model so it's baked into the image
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# --- Runtime stage ---
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /install /usr/local
COPY app/ ./app/
COPY docs/protocolos/ ./docs/protocolos/

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
