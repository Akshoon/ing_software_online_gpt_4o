# Procesador de Bibliografía de PDFs

Sistema para procesar archivos PDF de programas académicos y extraer información bibliográfica utilizando OpenAI.

## Configuración Inicial

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

1. Copia el archivo `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edita el archivo `.env` y añade tu clave de API de OpenAI:
   ```
   OPENAI_API_KEY=tu_clave_de_openai_aqui
   ```

   **Importante:** Nunca compartas tu archivo `.env` ni lo subas a Git. Este archivo está incluido en `.gitignore` para proteger tus claves.

### 3. Obtener una Clave de API de OpenAI

Si no tienes una clave de API de OpenAI:
1. Ve a [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Inicia sesión o crea una cuenta
3. Genera una nueva clave de API
4. Copia la clave y pégala en tu archivo `.env`

## Uso

### Modo CLI (Línea de Comandos)

```bash
python main.py
```

### Modo GUI (Interfaz Gráfica)

```bash
python gui.py
```

## Estructura del Proyecto

```
.
├── main.py              # Script principal (CLI)
├── gui.py               # Interfaz gráfica
├── models.py            # Modelos de base de datos
├── requirements.txt     # Dependencias del proyecto
├── .env                 # Variables de entorno (NO subir a Git)
├── .env.example         # Plantilla de variables de entorno
├── .gitignore           # Archivos ignorados por Git
└── archivos/            # Directorio para PDFs a procesar
```

## Seguridad

- ✅ Las claves de API están protegidas en el archivo `.env`
- ✅ El archivo `.env` está incluido en `.gitignore`
- ✅ Se proporciona `.env.example` como plantilla
- ⚠️ Nunca compartas tu archivo `.env` con nadie
- ⚠️ Nunca subas claves de API a repositorios públicos

## Notas

- El archivo `.env` debe estar en la raíz del proyecto
- Si obtienes un error sobre `OPENAI_API_KEY`, verifica que el archivo `.env` existe y contiene tu clave
