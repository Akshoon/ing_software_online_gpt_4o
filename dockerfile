# ── Stage 1: dependencias ────────────────────────────────────────
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema para compilar paquetes nativos
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt && \
    # pip-audit para A06 (escaneo de CVEs en dependencias)
    pip install --prefix=/install --no-cache-dir pip-audit


# ── Stage 2: imagen final ─────────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8012

WORKDIR /app

# Dependencias mínimas de runtime
# curl y wget se incluyen para que el script de pruebas de seguridad (trivy) pueda instalarse
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    ca-certificates \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Instalar trivy para A06 (escaneo de CVEs en imagen)
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    | sh -s -- -b /usr/local/bin 2>/dev/null || \
    echo "trivy install failed — escaneo manual necesario"

# Copiar paquetes instalados desde el stage builder (incluye pip-audit)
COPY --from=builder /install /usr/local

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/data /app/uploads

# Usuario no-root para seguridad
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8012

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8012/login')" || exit 1

# Gunicorn para producción
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8012", \
     "--workers", "2", \
     "--threads", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]
