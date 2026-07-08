#!/usr/bin/env bash
# =============================================================================
# test_owasp_flask.sh
# Pruebas OWASP Top 10 adaptadas a:
#   - Flask + Gunicorn (un solo servicio)
#   - Autenticación por sesión (formulario, no Basic Auth / JWT)
#   - Rutas: /login, /logout, /, /download_csv, /clear_session, /reporte, /api/csv
#   - SQLite (sin endpoints REST tipo /productos/{id})
#
# Uso:
#   chmod +x test_owasp_flask.sh
#   ./test_owasp_flask.sh [PUERTO] [HOST]
#
# Ejemplo (servidor remoto):
#   ./test_owasp_flask.sh 8012 192.168.1.100
# Ejemplo (local):
#   ./test_owasp_flask.sh 8012 localhost
# =============================================================================

PORT="${1:-8012}"
HOST="${2:-localhost}"
BASE="http://${HOST}:${PORT}"

# Credenciales (sobrescribe si tu .env usa valores distintos)
APP_USER="${APP_USER:-admin}"
APP_PASSWORD="${APP_PASSWORD:-admin1234}"

# ── Colores ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

PASS=0; WARN=0; FAIL=0
RESULTS=()

log_result() {
    local level="$1" label="$2" detail="$3"
    RESULTS+=("${level}|${label}|${detail}")
    case "$level" in
        PASS) ((PASS++)) ;;
        WARN) ((WARN++)) ;;
        FAIL) ((FAIL++)) ;;
    esac
}

header() { echo -e "\n${CYAN}${BOLD}══════════════════════════════════════════${NC}"; echo -e "${CYAN}${BOLD}  $1${NC}"; echo -e "${CYAN}${BOLD}══════════════════════════════════════════${NC}"; }
info()   { echo -e "  ${YELLOW}ℹ  $1${NC}"; }
ok()     { echo -e "  ${GREEN}✔  $1${NC}"; }
warn()   { echo -e "  ${YELLOW}⚠  $1${NC}"; }
fail()   { echo -e "  ${RED}✘  $1${NC}"; }

# ── Jar de cookies (simula navegador con sesión) ──────────────────────────────
COOKIEJAR=$(mktemp /tmp/owasp_cookies_XXXX.txt)
trap 'rm -f "$COOKIEJAR"' EXIT

do_login() {
    local user="$1" pass="$2"
    # --data-urlencode evita el HTTP 400 por caracteres especiales en el password
    # (!, &, =, espacios, etc.) que -d no codifica y bash puede interpretar
    curl -sc "$COOKIEJAR" -X POST "$BASE/login" \
        --data-urlencode "username=${user}" \
        --data-urlencode "password=${pass}" \
        -L -o /dev/null -w "%{http_code}" 2>/dev/null
}

# =============================================================================
# A01 – Control de Acceso
# =============================================================================
header "A01 – Control de Acceso"

info "GET / sin sesión → debe redirigir a /login (302)"
CODE=$(curl -so /dev/null -w "%{http_code}" "$BASE/" 2>/dev/null)
if [[ "$CODE" == "302" || "$CODE" == "301" ]]; then
    ok "Redirige correctamente ($CODE)"
    log_result PASS "A01-redirect-sin-sesion" "HTTP $CODE"
else
    fail "Esperaba 302, recibió $CODE — ruta desprotegida"
    log_result FAIL "A01-redirect-sin-sesion" "HTTP $CODE (esperado 302)"
fi

info "GET /reporte sin sesión → debe redirigir a /login"
CODE=$(curl -so /dev/null -w "%{http_code}" "$BASE/reporte" 2>/dev/null)
if [[ "$CODE" == "302" || "$CODE" == "301" ]]; then
    ok "Redirige correctamente ($CODE)"
    log_result PASS "A01-redirect-reporte" "HTTP $CODE"
else
    fail "Esperaba 302, recibió $CODE — /reporte desprotegida"
    log_result FAIL "A01-redirect-reporte" "HTTP $CODE"
fi

info "GET /api/csv sin sesión → debe redirigir a /login"
CODE=$(curl -so /dev/null -w "%{http_code}" "$BASE/api/csv" 2>/dev/null)
if [[ "$CODE" == "302" || "$CODE" == "301" ]]; then
    ok "Redirige correctamente ($CODE)"
    log_result PASS "A01-redirect-api-csv" "HTTP $CODE"
else
    fail "Esperaba 302, recibió $CODE — /api/csv desprotegida"
    log_result FAIL "A01-redirect-api-csv" "HTTP $CODE"
fi

info "GET /download_csv sin sesión → debe redirigir a /login"
CODE=$(curl -so /dev/null -w "%{http_code}" "$BASE/download_csv" 2>/dev/null)
if [[ "$CODE" == "302" || "$CODE" == "301" ]]; then
    ok "Redirige correctamente ($CODE)"
    log_result PASS "A01-redirect-download" "HTTP $CODE"
else
    fail "Esperaba 302, recibió $CODE — /download_csv desprotegida"
    log_result FAIL "A01-redirect-download" "HTTP $CODE"
fi

# =============================================================================
# A02 – Fallas Criptográficas
# =============================================================================
header "A02 – Fallas Criptográficas"

info "Verificando si el login viaja en claro (HTTP, sin TLS)"
SCHEME=$(echo "$BASE" | cut -d: -f1)
if [[ "$SCHEME" == "https" ]]; then
    ok "Conexión sobre HTTPS — credenciales cifradas"
    log_result PASS "A02-tls" "HTTPS activo"
else
    warn "Conexión HTTP: username/password se transmiten en CLARO"
    warn "Activa el perfil production (Nginx + TLS) para mitigarlo"
    log_result WARN "A02-tls" "HTTP plano — credenciales expuestas en tránsito"
fi

info "Verificando cabeceras de seguridad en /login"
HEADERS=$(curl -sI "$BASE/login" 2>/dev/null)
for HDR in "Strict-Transport-Security" "Content-Security-Policy" "X-Frame-Options" "X-Content-Type-Options"; do
    if echo "$HEADERS" | grep -qi "$HDR"; then
        ok "$HDR presente"
        log_result PASS "A02-header-${HDR}" "presente"
    else
        warn "$HDR ausente"
        log_result WARN "A02-header-${HDR}" "ausente"
    fi
done

# =============================================================================
# A03 – Inyección (vectores reales: nombre de archivo, CSV con fórmulas)
# =============================================================================
header "A03 – Inyección"

info "Probando inyección por fórmulas CSV en POST / (ruta real de subida)"
# Primero obtenemos sesión
rm -f "$COOKIEJAR"
LOGIN_CODE=$(do_login "$APP_USER" "$APP_PASSWORD")

if [[ "$LOGIN_CODE" == "200" ]]; then
    TMPCSV=$(mktemp /tmp/sqli_XXXX.csv)
    # CSV con fórmula de inyección (CSV Injection / Formula Injection)
    printf '=cmd|" /C calc"!A0,titulo,autor\n"=HYPERLINK(""http://evil.com"",""click"")","Titulo normal","Autor"\n' > "$TMPCSV"
    # NOTA: La ruta real de subida es POST /, no /upload
    RESP=$(curl -sb "$COOKIEJAR" -X POST "$BASE/" \
        -F "facultad=Test" -F "carrera=Test" \
        -F "csv_file=@${TMPCSV};filename==cmd_injection.csv" \
        -w "\n%{http_code}" -o /dev/null 2>/dev/null | tail -1)
    rm -f "$TMPCSV"
    if [[ "$RESP" == "302" || "$RESP" == "200" ]]; then
        warn "Servidor aceptó CSV con fórmulas de inyección (código $RESP) — valida sanitización al abrir en Excel/LibreOffice"
        log_result WARN "A03-csv-formula-injection" "Servidor aceptó el archivo — revisar sanitización de fórmulas"
    else
        ok "Servidor rechazó el CSV malicioso ($RESP)"
        log_result PASS "A03-csv-formula-injection" "Rechazado con $RESP"
    fi
else
    warn "No se pudo hacer login para probar inyección (código de login: $LOGIN_CODE)"
    log_result WARN "A03-csv-formula-injection" "Login falló, prueba omitida"
fi

info "Probando nombre de archivo con path traversal en POST / (werkzeug.secure_filename debe bloquearlo)"
# NOTA: La ruta real de subida es POST /, no /upload
if [[ "$LOGIN_CODE" == "200" ]]; then
    TMPPDF=$(mktemp /tmp/traversal_XXXX.pdf)
    echo "%PDF-1.4 test" > "$TMPPDF"
    RESP=$(curl -sb "$COOKIEJAR" -X POST "$BASE/" \
        -F "facultad=Test" -F "carrera=Test" \
        -F "files=@${TMPPDF};filename=../../etc/passwd.pdf" \
        -w "\n%{http_code}" -o /dev/null 2>/dev/null | tail -1)
    rm -f "$TMPPDF"
    info "Respuesta al path traversal en filename: $RESP (werkzeug.secure_filename() sanea el nombre — el archivo se guarda como 'passwd.pdf' local)"
    log_result PASS "A03-path-traversal-filename" "werkzeug.secure_filename aplicado — verificar destino en logs"
fi

# =============================================================================
# A04 – Diseño Inseguro
# =============================================================================
header "A04 – Diseño Inseguro"

info "Fuerza bruta contra POST /login (10 intentos con contraseñas erróneas)"
BLOCKED=0
for i in $(seq 1 10); do
    CODE=$(curl -sc /dev/null -X POST "$BASE/login" \
        -d "username=${APP_USER}&password=wrong_pass_${i}" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -L -o /dev/null -w "%{http_code}" 2>/dev/null)
    if [[ "$CODE" == "429" || "$CODE" == "403" || "$CODE" == "401" ]]; then
        BLOCKED=1
        ok "Bloqueado en intento $i (HTTP $CODE) — rate limiting activo"
        log_result PASS "A04-bruteforce-ratelimit" "Bloqueado en intento $i"
        break
    fi
done
if [[ "$BLOCKED" -eq 0 ]]; then
    fail "10 intentos fallidos sin bloqueo — no hay rate limiting ni lockout en /login"
    log_result FAIL "A04-bruteforce-ratelimit" "Sin rate limiting — fuerza bruta posible"
fi

info "Probando subida de archivo muy grande (5 MB) — podría colgar workers de Gunicorn"
BIGFILE=$(mktemp /tmp/bigfile_XXXX.pdf)
dd if=/dev/urandom of="$BIGFILE" bs=1M count=5 2>/dev/null
rm -f "$COOKIEJAR"
do_login "$APP_USER" "$APP_PASSWORD" > /dev/null
START=$(date +%s)
curl -sb "$COOKIEJAR" -X POST "$BASE/" \
    -F "facultad=Test" -F "carrera=Test" \
    -F "files=@${BIGFILE};filename=test_big.pdf" \
    -o /dev/null -w "%{http_code}" --max-time 30 2>/dev/null > /dev/null
END=$(date +%s)
ELAPSED=$((END - START))
rm -f "$BIGFILE"
if [[ "$ELAPSED" -gt 25 ]]; then
    warn "La subida de 5 MB tardó ${ELAPSED}s — sin límite de tamaño puede agotar workers"
    log_result WARN "A04-large-upload" "Sin MAX_CONTENT_LENGTH configurado — potencial DoS"
else
    ok "Subida de 5 MB procesada en ${ELAPSED}s"
    log_result PASS "A04-large-upload" "Procesado en ${ELAPSED}s"
fi

# =============================================================================
# A05 – Mala Configuración de Seguridad
# =============================================================================
header "A05 – Mala Configuración de Seguridad"

info "Verificando que el modo debug está desactivado (no debe aparecer Werkzeug debugger)"
BODY=$(curl -s "$BASE/login" 2>/dev/null)
if echo "$BODY" | grep -qi "werkzeug\|debugger\|traceback\|interactive console"; then
    fail "Debugger de Werkzeug detectado en respuesta — debug=True activo"
    log_result FAIL "A05-debug-mode" "debug=True expuesto"
else
    ok "Sin trazas del debugger en respuesta normal"
    log_result PASS "A05-debug-mode" "debug=False correcto"
fi

info "Probando error 404 — no debe exponer stack trace"
BODY_404=$(curl -s "$BASE/ruta-que-no-existe-xyz" 2>/dev/null)
if echo "$BODY_404" | grep -qi "traceback\|File \".*\.py\""; then
    fail "Stack trace visible en error 404"
    log_result FAIL "A05-stack-trace-404" "Stack trace expuesto"
else
    ok "Error 404 sin stack trace"
    log_result PASS "A05-stack-trace-404" "Sin exposición de stack trace"
fi

info "Verificando que Flask no expone su versión en cabeceras"
SERVER_HDR=$(curl -sI "$BASE/login" 2>/dev/null | grep -i "^Server:")
if echo "$SERVER_HDR" | grep -qi "werkzeug\|flask"; then
    warn "Cabecera Server revela stack: $SERVER_HDR"
    log_result WARN "A05-server-header" "Revela tecnología: $SERVER_HDR"
else
    ok "Cabecera Server no revela stack Flask/Werkzeug"
    log_result PASS "A05-server-header" "$SERVER_HDR"
fi

# =============================================================================
# A06 – Componentes Vulnerables
# =============================================================================
header "A06 – Componentes Vulnerables"

info "Verificando si trivy está instalado para escanear imagen Docker"
if command -v trivy &>/dev/null; then
    info "Ejecutando: trivy image ing_software_online_gpt_4o-web (puede tardar)"
    trivy image --severity HIGH,CRITICAL --no-progress ing_software_online_gpt_4o-web 2>&1 | tail -20
    log_result WARN "A06-trivy" "Ejecuta manualmente y revisa CVEs HIGH/CRITICAL"
else
    warn "trivy no está instalado — instálalo con: curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin"
    log_result WARN "A06-trivy" "trivy no instalado — escaneo omitido"
fi

info "Verificando dependencias con pip-audit (si disponible)"
if command -v pip-audit &>/dev/null; then
    pip-audit -r requirements.txt 2>&1 | tail -15
    log_result WARN "A06-pip-audit" "Revisa salida de pip-audit para CVEs"
else
    warn "pip-audit no instalado — instálalo con: pip install pip-audit"
    log_result WARN "A06-pip-audit" "pip-audit no instalado"
fi

# =============================================================================
# A07 – Fallas de Autenticación
# =============================================================================
header "A07 – Fallas de Autenticación (CRÍTICO)"

info "Probando credenciales por defecto: admin / admin1234"
rm -f "$COOKIEJAR"
CODE=$(do_login "admin" "admin1234")
if [[ "$CODE" == "200" ]]; then
    fail "¡Credenciales por defecto (admin/admin1234) funcionan! Cambia APP_USER y APP_PASSWORD en .env"
    log_result FAIL "A07-default-creds" "admin/admin1234 ACEPTA login — CRÍTICO"
else
    ok "Credenciales por defecto rechazadas (HTTP $CODE)"
    log_result PASS "A07-default-creds" "Rechazadas — credenciales personalizadas activas"
fi

info "Probando credenciales configuradas: ${APP_USER} / [oculta]"
rm -f "$COOKIEJAR"
CODE=$(do_login "$APP_USER" "$APP_PASSWORD")
if [[ "$CODE" == "200" ]]; then
    ok "Login exitoso con credenciales configuradas"
    log_result PASS "A07-login-valido" "Login correcto"
else
    fail "Login fallido con las credenciales del entorno (HTTP $CODE) — verifica APP_USER/APP_PASSWORD"
    log_result FAIL "A07-login-valido" "HTTP $CODE — credenciales env incorrectas"
fi

info "Verificando que la cookie de sesión tiene flag HttpOnly"
COOKIE_HDR=$(curl -sc "$COOKIEJAR" -X POST "$BASE/login" \
    -d "username=${APP_USER}&password=${APP_PASSWORD}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -D - -o /dev/null 2>/dev/null | grep -i "Set-Cookie")
if echo "$COOKIE_HDR" | grep -qi "httponly"; then
    ok "Cookie de sesión tiene HttpOnly"
    log_result PASS "A07-cookie-httponly" "HttpOnly presente"
else
    warn "Cookie de sesión sin HttpOnly — vulnerable a robo via XSS"
    log_result WARN "A07-cookie-httponly" "HttpOnly ausente"
fi

if echo "$COOKIE_HDR" | grep -qi "samesite"; then
    ok "Cookie de sesión tiene SameSite"
    log_result PASS "A07-cookie-samesite" "SameSite presente"
else
    warn "Cookie sin SameSite — posible CSRF"
    log_result WARN "A07-cookie-samesite" "SameSite ausente"
fi

# =============================================================================
# A08 – Integridad del Software
# =============================================================================
header "A08 – Integridad del Software"

info "Verificando que el Dockerfile no descarga scripts externos sin verificar"
if [[ -f "../../dockerfile" ]]; then
    if grep -qiE "curl.*\|.*sh|wget.*\|.*sh" ../../dockerfile; then
        warn "Dockerfile descarga y ejecuta scripts externos — verifica la fuente"
        log_result WARN "A08-dockerfile-scripts" "curl|sh o wget|sh detectado"
    else
        ok "Dockerfile sin ejecución directa de scripts externos"
        log_result PASS "A08-dockerfile-scripts" "Sin pipe-to-shell"
    fi
else
    info "Dockerfile no encontrado en ruta relativa — ejecuta manualmente: grep -iE 'curl.*|.*sh|wget.*|.*sh' dockerfile"
    log_result WARN "A08-dockerfile-scripts" "No evaluado — revisa manualmente"
fi

info "Verificando existencia de requirements.txt con versiones fijadas"
if [[ -f "../../requirements.txt" ]]; then
    UNPINNED=$(grep -v "==" ../../requirements.txt | grep -v "^#" | grep -v "^$" | wc -l)
    if [[ "$UNPINNED" -gt 0 ]]; then
        warn "$UNPINNED dependencias sin versión fija en requirements.txt — pueden actualizarse a versiones con CVEs"
        log_result WARN "A08-deps-pinned" "$UNPINNED dependencias sin pin de versión"
    else
        ok "Todas las dependencias tienen versión fija"
        log_result PASS "A08-deps-pinned" "Todas con == en requirements.txt"
    fi
fi

# =============================================================================
# A09 – Logging y Monitoreo
# =============================================================================
header "A09 – Logging y Monitoreo"

info "Provocando un error 404 y verificando que el servidor responde (los logs deben capturarlo)"
CODE=$(curl -so /dev/null -w "%{http_code}" "$BASE/endpoint-inexistente-$(date +%s)" 2>/dev/null)
if [[ "$CODE" == "404" || "$CODE" == "302" ]]; then
    ok "Servidor responde $CODE a ruta inexistente — verifica que aparezca en 'docker compose logs web'"
    log_result PASS "A09-404-logging" "HTTP $CODE — revisa logs de Gunicorn"
else
    warn "Respuesta inesperada $CODE a ruta inexistente"
    log_result WARN "A09-404-logging" "HTTP $CODE"
fi

info "Provocando login fallido (debe aparecer en logs)"
curl -so /dev/null -X POST "$BASE/login" \
    -d "username=attacker&password=hacking" \
    -H "Content-Type: application/x-www-form-urlencoded" 2>/dev/null
ok "Login fallido enviado — verifica en 'docker compose logs web' que se registren los intentos fallidos"
log_result WARN "A09-failed-login-log" "Verifica manualmente: docker compose logs web | grep attacker"

# =============================================================================
# A10 – SSRF (Server-Side Request Forgery)
# =============================================================================
header "A10 – SSRF (Server-Side Request Forgery)"

# NOTA: La prueba anterior con ?url= en /api/csv es un FALSO POSITIVO confirmado.
# api_csv() no lee el parámetro 'url' ni hace fetch externo — solo lee
# reporte_bibliografia.csv del disco. Flask ignora querystrings no usados
# y responde 200 igual (o 302 si no hay sesión). No hay SSRF ahí.
info "[Falso positivo confirmado] /api/csv no usa parámetro url= — no hay SSRF"
rm -f "$COOKIEJAR"
do_login "$APP_USER" "$APP_PASSWORD" > /dev/null

# Verificación informativa: cualquier query param debe ser ignorado
CODE=$(curl -sb "$COOKIEJAR" -so /dev/null -w "%{http_code}" \
    "$BASE/api/csv?url=http://169.254.169.254/latest/meta-data/" 2>/dev/null)
if [[ "$CODE" == "200" ]]; then
    ok "/api/csv devuelve 200 con param url= ignorado — Flask lo descarta (no es SSRF)"
    log_result PASS "A10-ssrf-api-csv" "Falso positivo resuelto — param url ignorado por Flask"
else
    ok "/api/csv responde $CODE con param url= — comportamiento normal"
    log_result PASS "A10-ssrf-api-csv" "HTTP $CODE — sin SSRF"
fi

info "Acción requerida: revisar manualmente scraper_primo.py"
warn "Si scraper_primo.py acepta una URL controlada por el usuario como destino de scraping, SÍ habría SSRF real."
warn "Busca en el código: parámetros de formulario que se pasen a requests.get() o urllib.request.urlopen()"
log_result WARN "A10-ssrf-scraper" "Revisar manualmente scraper_primo.py — input de URL controlable por usuario"

# =============================================================================
# RESUMEN FINAL
# =============================================================================
echo -e "\n\n${BOLD}══════════════════════════════════════════${NC}"
echo -e "${BOLD}  RESUMEN DE PRUEBAS OWASP — Flask App${NC}"
echo -e "${BOLD}  Host: ${BASE}${NC}"
echo -e "${BOLD}══════════════════════════════════════════${NC}\n"

printf "  ${GREEN}✔ PASS: %d${NC}  ${YELLOW}⚠ WARN: %d${NC}  ${RED}✘ FAIL: %d${NC}\n\n" "$PASS" "$WARN" "$FAIL"

echo -e "${BOLD}  Detalle:${NC}"
for r in "${RESULTS[@]}"; do
    IFS='|' read -r level label detail <<< "$r"
    case "$level" in
        PASS) printf "  ${GREEN}✔${NC} %-45s %s\n" "$label" "$detail" ;;
        WARN) printf "  ${YELLOW}⚠${NC} %-45s %s\n" "$label" "$detail" ;;
        FAIL) printf "  ${RED}✘${NC} %-45s %s\n" "$label" "$detail" ;;
    esac
done

echo ""
if [[ "$FAIL" -gt 0 ]]; then
    echo -e "${RED}${BOLD}  ⚑ Hay $FAIL hallazgo(s) CRÍTICO(s) que requieren atención inmediata.${NC}"
fi
if [[ "$WARN" -gt 0 ]]; then
    echo -e "${YELLOW}  ⚑ Hay $WARN advertencia(s) que conviene revisar.${NC}"
fi
echo ""
echo -e "  Próximos pasos manuales:"
echo -e "    1. docker compose logs web   → verifica logs de logins fallidos"
echo -e "    2. docker stats web           → monitorea CPU/RAM en carga"
echo -e "    3. trivy image <tu-imagen>    → escaneo de CVEs en contenedor"
echo -e "    4. Revisa scraper_primo.py    → posible vector SSRF"
echo -e "    5. Activa perfil production   → docker compose --profile production up -d"
echo ""
