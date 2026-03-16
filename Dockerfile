# ── Stage 1: Build React frontend ──────────────────────────
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit --no-fund 2>/dev/null || npm install --no-audit --no-fund
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python runtime ───────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install Python dependencies first (cacheable layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null; \
    # PyAudio is optional (not needed on Cloud Run) — ignore install failures
    true

# Copy application code
COPY . .

# Copy the built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

EXPOSE 8080

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8080/health'); r.raise_for_status()" || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
