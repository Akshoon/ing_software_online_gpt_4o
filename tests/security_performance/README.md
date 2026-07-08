# Tests de Seguridad y Rendimiento

Pruebas adaptadas a la arquitectura real del proyecto:
- **Flask + Gunicorn** (2 workers, 4 threads, puerto 8012)
- **Autenticación por sesión** (formulario `username`/`password`, no Basic Auth)
- **SQLite** (sin endpoints REST tipo `/productos/{id}`)

## Archivos

| Archivo | Propósito |
|---|---|
| `test_owasp_flask.sh` | OWASP Top 10 completo — pruebas de seguridad |
| `test_rendimiento.sh` | Latencia (curl), carga (wrk), docker stats |
| `locustfile.py` | Carga sostenida con sesión real (Locust) |

---

## Requisitos

```bash
# Herramientas externas (Linux/WSL/servidor)
sudo apt-get install curl wrk       # curl ya suele estar, wrk para carga básica
pip install locust                  # carga con sesión real
pip install pip-audit               # escaneo de dependencias (opcional)

# trivy (escaneo de imagen Docker) — opcional
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
  | sh -s -- -b /usr/local/bin
```

> ⚠️ **Ejecutar desde Linux/WSL/servidor** — los `.sh` requieren bash. En Windows usa WSL o Git Bash.

---

## Uso rápido

### 1. Pruebas OWASP (seguridad)

```bash
# Con la app corriendo:
docker compose up -d

chmod +x tests/security_performance/test_owasp_flask.sh

# Local:
./tests/security_performance/test_owasp_flask.sh 8012 localhost

# Servidor remoto:
./tests/security_performance/test_owasp_flask.sh 8012 192.168.1.100

# Credenciales personalizadas:
APP_USER=miusuario APP_PASSWORD=mipass ./tests/security_performance/test_owasp_flask.sh 8012 localhost
```

### 2. Pruebas de rendimiento

```bash
chmod +x tests/security_performance/test_rendimiento.sh
./tests/security_performance/test_rendimiento.sh 8012 localhost
```

### 3. Carga sostenida con Locust

```bash
# Modo headless (recomendado para CI/informes)
export APP_USER=admin APP_PASSWORD=admin1234
locust -f tests/security_performance/locustfile.py \
       --host http://localhost:8012 \
       --headless -u 20 -r 5 --run-time 60s \
       --html reporte_carga.html --csv resultados_carga

# Modo UI interactivo (abre http://localhost:8089)
locust -f tests/security_performance/locustfile.py --host http://localhost:8012
```

**Perfiles de carga sugeridos** (Gunicorn: 2 workers × 4 threads = 8 concurrentes máx):

| Escenario | `-u` | `-r` | `--run-time` | Expectativa |
|---|---|---|---|---|
| Baseline | 8 | 2 | 60s | Sin errores, P95 < 500ms |
| Carga media | 20 | 5 | 120s | < 1% errores |
| Pico | 50 | 10 | 60s | Errores 503 esperados |

---

## Hallazgos conocidos (revisar antes de producción)

| # | Categoría | Riesgo | Estado |
|---|---|---|---|
| A04 | Sin rate limiting en `/login` | ALTO | ⚠️ Sin fix |
| A07 | Credenciales por defecto `admin/admin1234` en `.env` | ALTO | ⚠️ Cambiar en prod |
| A02 | Sin TLS en perfil `dev` (HTTP plano) | MEDIO | ℹ️ Activa perfil `production` |
| A08 | Dependencias sin versión fija en `requirements.txt` | MEDIO | ⚠️ Fijar con `==` |
| A04 | Sin `MAX_CONTENT_LENGTH` en Flask | MEDIO | ⚠️ Riesgo DoS por archivos grandes |

---

## Qué mide cada categoría OWASP

| OWASP | Qué prueba en esta app |
|---|---|
| **A01** | Todas las rutas protegidas redirigen 302 sin cookie |
| **A02** | TLS activo, cabeceras de seguridad (HSTS, CSP, X-Frame-Options) |
| **A03** | CSV con fórmulas (`=cmd`), path traversal en `filename=` |
| **A04** | Fuerza bruta sin lockout, subida de archivos grandes (DoS) |
| **A05** | `debug=False`, stack traces, cabecera `Server:` |
| **A06** | `trivy image`, `pip-audit -r requirements.txt` |
| **A07** | Credenciales por defecto, cookie `HttpOnly`/`SameSite` |
| **A08** | Dockerfile sin `curl \| sh`, dependencias con pin de versión |
| **A09** | Logs de 404 y logins fallidos en Gunicorn |
| **A10** | Parámetros de URL en `/api/csv`, revisar `scraper_primo.py` |
