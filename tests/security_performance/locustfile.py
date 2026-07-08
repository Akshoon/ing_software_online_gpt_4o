"""
locustfile.py — Pruebas de carga adaptadas a Flask + sesión de formulario
=========================================================================
Simula usuarios reales que:
  1. Hacen login con username/password (POST /login) para obtener cookie de sesión
  2. Navegan por las rutas protegidas: /, /reporte, /api/csv, /download_csv

Uso:
  pip install locust
  export APP_USER=admin APP_PASSWORD=tu_password_real

  # Modo headless (terminal):
  locust -f locustfile.py --host http://localhost:8012 \\
         --headless -u 20 -r 5 --run-time 60s \\
         --html reporte_carga.html --csv resultados_carga

  # Modo UI (abre http://localhost:8089):
  locust -f locustfile.py --host http://localhost:8012

Parámetros de carga sugeridos para un Gunicorn con 2 workers 4 threads:
  Baseline:    -u 8   -r 2   --run-time 60s
  Carga media: -u 20  -r 5   --run-time 120s
  Pico:        -u 50  -r 10  --run-time 60s  (espera errores 500/503)
"""
import os
import random
from locust import HttpUser, task, between, events

# ── Credenciales (ajusta en .env o como variables de entorno) ─────────────────
APP_USER     = os.environ.get("APP_USER", "admin")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "admin1234")


class FlaskSessionUser(HttpUser):
    """
    Usuario que mantiene una sesión Flask a través de cookies.
    Locust usa requests.Session internamente, así que las cookies
    se persisten automáticamente entre requests del mismo usuario.
    """
    wait_time = between(1, 3)   # pausa realista entre peticiones (segundos)
    _logged_in = False

    # ── Setup: login al comenzar ──────────────────────────────────────────────
    def on_start(self):
        """Se ejecuta una vez por usuario virtual al arrancar."""
        self._do_login()

    def _do_login(self):
        """POST /login con formulario. Guarda cookie de sesión en self.client."""
        with self.client.post(
            "/login",
            data={"username": APP_USER, "password": APP_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            allow_redirects=True,
            name="/login [setup]",
            catch_response=True,
        ) as resp:
            # Flask redirige a / si el login es correcto
            if resp.status_code == 200 and "login" not in resp.url:
                self._logged_in = True
                resp.success()
            elif resp.status_code == 200 and "error" in resp.text.lower():
                self._logged_in = False
                resp.failure(f"Login falló — credenciales incorrectas. URL final: {resp.url}")
            else:
                self._logged_in = True   # asumimos éxito si no hay error explícito
                resp.success()

    # ── Tareas principales ────────────────────────────────────────────────────

    @task(3)
    def visit_index(self):
        """GET / — página de carga de archivos (más frecuente)."""
        with self.client.get("/", name="GET /", catch_response=True) as resp:
            if resp.status_code == 302 and "/login" in resp.headers.get("Location", ""):
                # Sesión expiró → re-login
                resp.failure("Sesión expirada en GET /")
                self._do_login()
            elif resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(2)
    def visit_reporte(self):
        """GET /reporte — visualización del CSV (frecuente)."""
        with self.client.get("/reporte", name="GET /reporte", catch_response=True) as resp:
            if resp.status_code == 302:
                resp.failure("Sesión expirada en GET /reporte")
                self._do_login()
            elif resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(3)
    def api_csv_json(self):
        """GET /api/csv — endpoint JSON con datos del reporte (más frecuente, simula AJAX)."""
        with self.client.get("/api/csv", name="GET /api/csv", catch_response=True) as resp:
            if resp.status_code == 302:
                resp.failure("Sesión expirada en GET /api/csv")
                self._do_login()
            elif resp.status_code == 200:
                try:
                    data = resp.json()
                    if "exists" in data:
                        resp.success()
                    else:
                        resp.failure("JSON sin campo 'exists'")
                except Exception as e:
                    resp.failure(f"JSON inválido: {e}")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(1)
    def download_csv(self):
        """GET /download_csv — descarga del CSV (menos frecuente)."""
        with self.client.get(
            "/download_csv", name="GET /download_csv",
            stream=True, catch_response=True
        ) as resp:
            if resp.status_code == 302 and "/login" in resp.headers.get("Location", ""):
                resp.failure("Sesión expirada en GET /download_csv")
                self._do_login()
            elif resp.status_code in (200, 302):
                # 302 a / si no existe el CSV es comportamiento esperado
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(1)
    def login_page(self):
        """GET /login — mide latencia de la página de login (sin sesión)."""
        # Abrimos una sesión nueva (sin cookie) para medir la página en frío
        with self.client.get("/login", name="GET /login [cold]", catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 302:
                # Si ya hay sesión activa, redirige a / → también es éxito
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    # ── Cleanup ───────────────────────────────────────────────────────────────
    def on_stop(self):
        """Logout al terminar cada usuario virtual."""
        self.client.get("/logout", name="GET /logout [teardown]", catch_response=False)


# ── Clase separada: usuario anónimo (mide redirects sin sesión) ───────────────
class AnonymousUser(HttpUser):
    """
    Usuario sin sesión. Solo mide el comportamiento del redirect de /login_required.
    Útil para verificar que las rutas protegidas redirigen y no dan 200.
    """
    wait_time = between(2, 5)
    weight = 1   # 1 usuario anónimo por cada N FlaskSessionUser

    @task
    def probe_protected_routes(self):
        routes = ["/", "/reporte", "/api/csv", "/download_csv"]
        route = random.choice(routes)
        with self.client.get(
            route, name=f"GET {route} [anon]",
            allow_redirects=False, catch_response=True
        ) as resp:
            if resp.status_code in (301, 302):
                resp.success()   # redirect a /login es el comportamiento correcto
            elif resp.status_code == 200:
                resp.failure(f"Ruta {route} accesible sin sesión — A01 violation")
            else:
                resp.success()   # cualquier otro código (404, 405) es aceptable


# ── Hooks de eventos para logging adicional ───────────────────────────────────
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print(f"\n[locust] Iniciando prueba de carga contra: {environment.host}")
    print(f"[locust] APP_USER={APP_USER} | APP_PASSWORD={'*' * len(APP_PASSWORD)}")
    print(f"[locust] Rutas objetivo: /login, /, /reporte, /api/csv, /download_csv\n")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats.total
    print(f"\n[locust] ── Resumen ──────────────────────────────────────────")
    print(f"[locust] Total requests : {stats.num_requests}")
    print(f"[locust] Failures       : {stats.num_failures}")
    print(f"[locust] Median (ms)    : {stats.median_response_time}")
    print(f"[locust] P95 (ms)       : {stats.get_response_time_percentile(0.95)}")
    print(f"[locust] P99 (ms)       : {stats.get_response_time_percentile(0.99)}")
    print(f"[locust] RPS avg        : {stats.current_rps:.1f}")
    print(f"[locust] ────────────────────────────────────────────────────\n")
