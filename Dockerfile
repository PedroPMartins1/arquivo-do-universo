FROM node:22-bookworm-slim AS frontend
WORKDIR /build/frontend
RUN npm install --global pnpm@9.15.9
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

FROM python:3.12-slim-bookworm AS backend
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl unzip ca-certificates && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==0.13.9
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/src/ src/
RUN uv sync --locked --no-dev --no-editable
COPY backend/scripts/ scripts/
ENV ARQUIVO_EPHEMERIS_PATH=/app/data/ephe ARQUIVO_GEONAMES_PATH=/app/data/geonames
RUN bash scripts/fetch_ephemerides.sh && bash scripts/fetch_places.sh --download-only

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 ca-certificates && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home arquivo
WORKDIR /app/backend
ENV PATH="/app/backend/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    ARQUIVO_EPHEMERIS_PATH=/app/data/ephe \
    ARQUIVO_GEONAMES_PATH=/app/data/geonames \
    ARQUIVO_FRONTEND_PATH=/app/frontend/dist
COPY --from=backend /app/backend/.venv/ .venv/
COPY --from=backend /app/data/ /app/data/
COPY --from=frontend /build/frontend/dist/ /app/frontend/dist/
COPY backend/alembic.ini ./
COPY backend/migrations/ migrations/
COPY deploy/start.py /app/deploy/start.py
USER arquivo
EXPOSE 10000
CMD ["python", "/app/deploy/start.py"]
