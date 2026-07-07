# Guía de Despliegue en Producción

Esta guía explica paso a paso cómo levantar el sistema **Procesador de Bibliografía Académica** en un servidor **Ubuntu** utilizando **Docker y Docker Compose** (método recomendado), así como en plataformas cloud como Railway o Render.

---

## 🚀 Despliegue en Servidor Ubuntu (Recomendado)

El proyecto ya está completamente dockerizado con un `Dockerfile` optimizado multi-stage y un `docker-compose.yml` que configura **Gunicorn (WSGI para producción)** y volúmenes para la persistencia de la base de datos (`sqlite`) y reportes CSV.

### Paso 1: Instalar Docker y Docker Compose en Ubuntu
Conéctate por SSH a tu servidor Ubuntu y ejecuta los siguientes comandos para instalar Docker y el plugin oficial de Compose:

```bash
# 1. Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar Docker y herramientas necesarias
sudo apt install -y curl git docker.io docker-compose-v2

# 3. Habilitar e iniciar el servicio de Docker
sudo systemctl enable docker
sudo systemctl start docker

# 4. (Opcional) Agregar tu usuario actual al grupo docker para no usar 'sudo' en cada comando
sudo usermod -aG docker $USER
newgrp docker
```

### Paso 2: Clonar el repositorio y configurar entorno
Clona el proyecto en tu servidor (o sube tus archivos por SSH/SFTP) y prepara las variables de entorno:

```bash
# 1. Clonar el proyecto (reemplaza con la URL de tu repositorio)
git clone <URL_DE_TU_REPOSITORIO> bibliografia_app
cd bibliografia_app

# 2. Crear el archivo .env desde el ejemplo
cp .env.example .env

# 3. Editar el archivo .env con tu editor favorito (nano o vim)
nano .env
```

**Configuración obligatoria en tu archivo `.env`:**
```ini
# API Keys de Inteligencia Artificial
OPENAI_API_KEY=tu_clave_de_openai_aqui
GEMINI_API_KEY=tu_clave_de_gemini_aqui
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-3.5-flash

# Credenciales de acceso web (¡IMPORTANTE CAMBIAR EN PRODUCCIÓN!)
SECRET_KEY=clave-secreta-ultra-segura-aleatoria-para-produccion
APP_USER=admin
APP_PASSWORD=tu_contraseña_segura_aqui
```
*(Guarda en nano presionando `CTRL + O`, luego `Enter`, y sal con `CTRL + X`).*

---

### Paso 3: Levantar la aplicación con Docker Compose

Para construir y levantar el contenedor en segundo plano (*detached mode*), ejecuta:

```bash
docker compose up -d --build
```

#### ¿Qué está sucediendo bajo el capó?
1. **Construcción Multi-stage:** Se compilarán las dependencias en una imagen limpia y compacta.
2. **Servidor Gunicorn:** La aplicación se ejecutará con `gunicorn` (2 workers, 4 threads, timeout de 120s para procesar PDFs sin que se corte la conexión).
3. **Volúmenes Persistentes:** Se crearán automáticamente los volúmenes de Docker para que tu base de datos SQLite (`/app/data`) y el archivo CSV (`reporte_bibliografia.csv`) **nunca se borren**, incluso si reinicias o actualizas el contenedor.
4. **Healthcheck:** El contenedor comprobará periódicamente que el endpoint `/login` responde correctamente.

---

### Paso 4: Verificar que todo está funcionando

Puedes comprobar el estado y los registros de tu aplicación con:

```bash
# Ver el estado de los contenedores y el healthcheck
docker compose ps

# Ver los logs en tiempo real (útil para depurar)
docker compose logs -f web
```

Tu aplicación ya estará accesible desde el navegador en el puerto 8012 de tu servidor:
👉 **`http://<IP_DE_TU_SERVIDOR_UBUNTU>:8012`**

---

### Paso 4.1: Habiliar el puerto 8012 en el Firewall (iptables / UFW)

Si no puedes acceder desde tu navegador, es muy probable que el firewall de Ubuntu o de tu proveedor de nube esté bloqueando el puerto **8012**. Aquí tienes los comandos para abrirlo:

#### Opción A: Usando `iptables` (Firewall tradicional de Linux)
```bash
# 1. Permitir el tráfico entrante TCP en el puerto 8012
sudo iptables -I INPUT -p tcp --dport 8012 -j ACCEPT

# 2. Guardar las reglas para que persistan tras reiniciar el servidor
# En Ubuntu/Debian se utiliza iptables-persistent:
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
```

#### Opción B: Usando `UFW` (Uncomplicated Firewall - el más común en Ubuntu)
```bash
# 1. Permitir el puerto 8012
sudo ufw allow 8012/tcp

# 2. Verificar el estado del firewall y las reglas activas
sudo ufw status verbose
```

> [!IMPORTANT]
> **¿Estás usando un proveedor de nube (AWS, GCP, Azure, Oracle Cloud, DigitalOcean)?**
> Además de ejecutar `iptables` o `ufw` en la consola de Ubuntu, **debes abrir el puerto 8012 en el panel web de tu proveedor** (en la sección de *Security Groups*, *Firewall Rules* o *Listas de Seguridad* de tu VPC).

---

### Paso 5 (Opcional): Configurar Nginx y HTTPS (Dominio y SSL)

Si vas a usar un nombre de dominio (ej. `bibliografia.miuniversidad.edu`) y el puerto 80/443:

1. El proyecto ya incluye un archivo `nginx.conf` preconfigurado con soporte para subida de archivos grandes (100 MB) y timeouts largos (120s).
2. Para levantar la aplicación junto con el proxy Nginx en el puerto 80, utiliza el perfil de producción:

```bash
docker compose --profile production up -d
```
*(Asegúrate de tener los puertos 80 y 443 abiertos en el firewall de tu servidor: `sudo ufw allow 80,443/tcp`).*

---

## 🛠️ Mantenimiento y Comandos Útiles

| Acción | Comando |
| :--- | :--- |
| **Detener la aplicación** | `docker compose down` |
| **Reiniciar la aplicación** | `docker compose restart` |
| **Actualizar el código (tras un git pull)** | `docker compose up -d --build` |
| **Ver uso de recursos (RAM/CPU)** | `docker stats` |
| **Entrar a la consola del contenedor** | `docker exec -it bibliografia_app bash` |

---

## ☁️ Despliegue en Plataformas Cloud (Alternativa)

### Railway
1. Crea un nuevo proyecto en [railway.app](https://railway.app/) desde tu repositorio de GitHub.
2. En la pestaña **Variables**, agrega: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `APP_USER`, `APP_PASSWORD` y `SECRET_KEY`.
3. Railway detectará el `Dockerfile` y levantará el contenedor de forma automática.
*(Nota: Para que la base de datos SQLite persista en Railway, debes adjuntar un **Volume** y montarlo en `/app/data`).*

### Render
1. En [render.com](https://render.com/), selecciona **New + -> Web Service** conectado a tu repo.
2. Selecciona **Runtime: Docker**.
3. Configura las variables de entorno (`APP_USER`, `APP_PASSWORD`, `SECRET_KEY`, API Keys).
4. Para persistencia, agrega un **Persistent Disk** montado en `/app/data`.
