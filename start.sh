#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
#  start.sh — Script de arranque automático
#  Procesador de Bibliografía Académica
# ═══════════════════════════════════════════════════════════════════

set -e  # Detener ante cualquier error

# ── Colores para la terminal ────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # Sin color

# Directorio raíz del proyecto (donde está este script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}║    Procesador de Bibliografía Académica              ║${NC}"
echo -e "${CYAN}${BOLD}║    Script de arranque automático                     ║${NC}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# ── 1. Verificar que Docker esté instalado ──────────────────────────
echo -e "${YELLOW}[1/5] Verificando Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker no está instalado. Instálalo con:${NC}"
    echo "  sudo apt install -y docker.io docker-compose-v2"
    exit 1
fi
echo -e "${GREEN}✔ Docker encontrado: $(docker --version)${NC}"

# ── 2. Verificar que el servicio Docker esté activo ─────────────────
echo -e "${YELLOW}[2/5] Verificando servicio Docker...${NC}"
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}  → Docker no está activo. Iniciando servicio...${NC}"
    sudo systemctl start docker
    sleep 2
fi
echo -e "${GREEN}✔ Docker activo y listo.${NC}"

# ── 3. Verificar/crear el archivo .env ─────────────────────────────
echo -e "${YELLOW}[3/5] Verificando archivo .env...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠  Archivo .env creado desde .env.example.${NC}"
        echo -e "${YELLOW}   Por favor, edita .env con tus API keys antes de continuar.${NC}"
        echo -e "${YELLOW}   Abre el archivo con:  nano .env${NC}"
        echo ""
        read -p "¿Ya configuraste el archivo .env? (s/N): " confirm
        if [[ ! "$confirm" =~ ^[sS]$ ]]; then
            echo -e "${RED}Operación cancelada. Configura .env primero.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ No se encontró .env ni .env.example. Crea el archivo .env manualmente.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✔ Archivo .env encontrado.${NC}"
fi

# ── 4. Detectar modo de despliegue (básico o producción con Nginx) ──
echo -e "${YELLOW}[4/5] Seleccionando modo de despliegue...${NC}"
echo ""
echo -e "  ${BOLD}[1]${NC} Modo estándar  — Solo app en puerto ${CYAN}8012${NC} (recomendado para desarrollo/pruebas)"
echo -e "  ${BOLD}[2]${NC} Modo producción — App + Nginx en puertos ${CYAN}8080${NC} (HTTP) y ${CYAN}8443${NC} (HTTPS)"
echo ""
read -p "Selecciona una opción [1/2] (default: 1): " mode
mode="${mode:-1}"

# ── 5. Levantar con Docker Compose ─────────────────────────────────
echo ""
echo -e "${YELLOW}[5/5] Construyendo y levantando contenedores...${NC}"
echo ""

if [ "$mode" = "2" ]; then
    echo -e "${CYAN}→ Modo producción (con Nginx)${NC}"
    docker compose --profile production up -d --build
    echo ""
    echo -e "${GREEN}${BOLD}✔ Aplicación levantada correctamente.${NC}"
    echo ""
    echo -e "  🌐 HTTP:  ${CYAN}http://$(hostname -I | awk '{print $1}'):8080${NC}"
    echo -e "  🔒 HTTPS: ${CYAN}https://$(hostname -I | awk '{print $1}'):8443${NC}"
else
    echo -e "${CYAN}→ Modo estándar${NC}"
    docker compose up -d --build
    echo ""
    echo -e "${GREEN}${BOLD}✔ Aplicación levantada correctamente.${NC}"
    echo ""
    echo -e "  🌐 URL:   ${CYAN}http://$(hostname -I | awk '{print $1}'):8012${NC}"
fi

echo ""
echo -e "${YELLOW}── Comandos útiles ───────────────────────────────────────${NC}"
echo -e "  Ver logs en tiempo real: ${BOLD}docker compose logs -f web${NC}"
echo -e "  Ver estado:              ${BOLD}docker compose ps${NC}"
echo -e "  Detener la app:          ${BOLD}docker compose down${NC}"
echo -e "  Reiniciar:               ${BOLD}docker compose restart${NC}"
echo -e "${YELLOW}─────────────────────────────────────────────────────────${NC}"
echo ""
