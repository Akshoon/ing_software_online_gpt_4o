#!/usr/bin/env bash
# =============================================================================
# test_rendimiento.sh
# Pruebas de rendimiento (latencia + carga básica con wrk) para Flask/Gunicorn
#
# Requisitos: curl, wrk (opcional), docker
# Uso: ./test_rendimiento.sh [PUERTO] [HOST]
# =============================================================================

PORT="${1:-8012}"
HOST="${2:-localhost}"
BASE="http://${HOST}:${PORT}"
APP_USER="${APP_USER:-admin}"
APP_PASSWORD="${APP_PASSWORD:-admin1234}"

CYAN='\033[0;36m'; BOLD='\033[1m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

header() { echo -e "\n${CYAN}${BOLD}══════════════════════════════════════════${NC}"; echo -e "${CYAN}${BOLD}  $1${NC}"; echo -e "${CYAN}${BOLD}══════════════════════════════════════════${NC}"; }

COOKIEJAR=$(mktemp /tmp/perf_cookies_XXXX.txt)
trap 'rm -f "$COOKIEJAR"' EXIT

# ── 1. Latencia con curl -w ───────────────────────────────────────────────────
header "1. Latencia por endpoint (curl -w timing)"

# Login primero para obtener cookie
curl -sc "$COOKIEJAR" -X POST "$BASE/login" \
    -d "username=${APP_USER}&password=${APP_PASSWORD}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -L -o /dev/null -w "" 2>/dev/null

FORMAT="\n  DNS:        %{time_namelookup}s\n  Conectar:   %{time_connect}s\n  TTFB:       %{time_starttransfer}s\n  Total:      %{time_total}s\n  HTTP:       %{http_code}\n"

for ENDPOINT in "/" "/reporte" "/api/csv" "/login"; do
    echo -e "\n  ${BOLD}→ $BASE$ENDPOINT${NC}"
    if [[ "$ENDPOINT" == "/login" ]]; then
        curl -so /dev/null -w "$FORMAT" "$BASE$ENDPOINT" 2>/dev/null
    else
        curl -sb "$COOKIEJAR" -so /dev/null -w "$FORMAT" "$BASE$ENDPOINT" 2>/dev/null
    fi
done

# ── 2. wrk en /login (única ruta sin requerir sesión) ────────────────────────
header "2. Carga con wrk (GET /login — no requiere sesión)"

if command -v wrk &>/dev/null; then
    echo -e "  ${YELLOW}wrk -t4 -c20 -d30s $BASE/login${NC}"
    wrk -t4 -c20 -d30s "$BASE/login"
else
    echo -e "  ${YELLOW}wrk no instalado.${NC} Instala con:"
    echo -e "    sudo apt-get install wrk    # Debian/Ubuntu"
    echo -e "    brew install wrk            # macOS"
    echo -e "  Para carga con sesión usa: locust -f locustfile.py"
fi

# ── 3. wrk con cookie (requiere Lua script) ───────────────────────────────────
header "3. Carga con wrk + cookie de sesión"

if command -v wrk &>/dev/null; then
    # Extrae el valor de la cookie de sesión
    SESSION_COOKIE=$(grep "session" "$COOKIEJAR" | awk '{print $NF}' | head -1)
    if [[ -n "$SESSION_COOKIE" ]]; then
        LUASCRIPT=$(mktemp /tmp/wrk_cookie_XXXX.lua)
        cat > "$LUASCRIPT" <<LUAEOF
wrk.headers["Cookie"] = "session=${SESSION_COOKIE}"
LUAEOF
        echo -e "  Carga en GET /reporte con cookie de sesión (30s, 4 threads, 20 conns)"
        wrk -t4 -c20 -d30s -s "$LUASCRIPT" "$BASE/reporte"
        echo ""
        echo -e "  Carga en GET /api/csv con cookie de sesión (30s, 4 threads, 20 conns)"
        wrk -t4 -c20 -d30s -s "$LUASCRIPT" "$BASE/api/csv"
        rm -f "$LUASCRIPT"
    else
        echo -e "  ${YELLOW}No se pudo extraer cookie de sesión. Verifica las credenciales.${NC}"
    fi
else
    echo -e "  ${YELLOW}wrk no disponible — usa locustfile.py para carga con sesión${NC}"
fi

# ── 4. docker stats (snapshot) ───────────────────────────────────────────────
header "4. Uso de recursos — docker stats (snapshot)"

if command -v docker &>/dev/null; then
    echo -e "  ${BOLD}Snapshot de contenedores activos:${NC}\n"
    docker stats --no-stream --format \
        "  {{.Name}}\tCPU: {{.CPUPerc}}\tRAM: {{.MemUsage}}\tNET: {{.NetIO}}\tDISK: {{.BlockIO}}" \
        2>/dev/null || echo "  (No hay contenedores corriendo o docker no está disponible)"
    echo ""
    echo -e "  Para monitoreo continuo: ${YELLOW}docker stats web${NC}"
    echo -e "  Para monitoreo durante carga (otra terminal): ${YELLOW}watch -n1 docker stats --no-stream${NC}"
else
    echo -e "  ${YELLOW}docker no disponible en PATH${NC}"
fi

# ── 5. Gunicorn worker saturation test ───────────────────────────────────────
header "5. Saturación de workers Gunicorn (2 workers × 4 threads = 8 concurrent max)"

echo -e "  Enviando 16 requests concurrentes (2× la capacidad) para detectar queuing...\n"
START=$(date +%s%N)
for i in $(seq 1 16); do
    curl -sb "$COOKIEJAR" -so /dev/null "$BASE/api/csv" &
done
wait
END=$(date +%s%N)
ELAPSED=$(( (END - START) / 1000000 ))
echo -e "  16 requests concurrentes completados en: ${BOLD}${ELAPSED}ms${NC}"
if [[ "$ELAPSED" -gt 5000 ]]; then
    echo -e "  ${YELLOW}⚠ >5s — posible queuing. Considera aumentar workers/threads en Gunicorn.${NC}"
else
    echo -e "  ${GREEN}✔ Dentro del rango esperado (<5s).${NC}"
fi

echo -e "\n${BOLD}  Para carga sostenida con usuarios reales, usa:${NC}"
echo -e "  ${CYAN}locust -f locustfile.py --host $BASE --headless -u 20 -r 5 --run-time 60s --html reporte_carga.html${NC}\n"
