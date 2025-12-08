# Procesador de Bibliografía Académica Inteligente

Sistema automatizado para la gestión, extracción y validación de bibliografías de programas de asignaturas universitarios. Utiliza Inteligencia Artificial (OpenAI GPT y Google Gemini) y Web Scraping para digitalizar, procesar y enriquecer la información bibliográfica.

## Características Principales

*   **Extracción Inteligente**: Extrae asignaturas, planes, semestres y listas bibliográficas desde archivos PDF y Word (syllabus).
*   **IA Híbrida**: Combina GPT-3.5/4 y Gemini Pro/Flash para maximizar precisión y minimizar costos. Lógica de fallback y balanceo de carga.
*   **Web Scraping Automatizado**: Verifica la disponibilidad física y digital de los libros en el catálogo de biblioteca (Primo/Aleph) en tiempo real.
*   **Normalización de Datos**: Estandariza autores y títulos, completando metadatos faltantes.
*   **Multi-Interfaz**:
    *   **Web App**: Interfaz moderna para carga y gestión remota.
    *   **GUI de Escritorio**: Aplicación nativa para uso local.
    *   **CLI**: Herramienta de línea de comandos para automatización y scripts.
*   **Reportes de Gestión**: Genera reportes detallados en CSV para la toma de decisiones sobre adquisiciones.

## Requisitos del Sistema

*   Python 3.8 o superior
*   Google Chrome (para el scraper Selenium)
*   Claves de API para:
    *   OpenAI (`OPENAI_API_KEY`)
    *   Google Gemini (`GEMINI_API_KEY`)

## Instalación

1.  **Clonar el repositorio**:
    ```bash
    git clone <url-del-repositorio>
    cd ing_software_online_gpt_4o
    ```

2.  **Crear y activar entorno virtual**:
    ```bash
    python -m venv venv
    # En Windows:
    .\venv\Scripts\activate
    # En Mac/Linux:
    source venv/bin/activate
    ```

3.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuración (.env)**:
    Crea un archivo `.env` en la raíz del proyecto con tus credenciales:
    ```env
    OPENAI_API_KEY=tu_clave_openai_aqui
    GEMINI_API_KEY=tu_clave_gemini_aqui
    # Opcionales
    OPENAI_MODEL=gpt-3.5-turbo
    ```

## Uso

### 1. Aplicación Web (Recomendado)
Interfaz amigable accesible desde el navegador.

```bash
python app.py
```
Accede a: `http://localhost:5000`

### 2. Interfaz de Escritorio (GUI)
Para usuarios que prefieren aplicaciones de ventana.

```bash
python -m src.gui
```

### 3. Línea de Comandos (CLI)
Para procesamiento rápido o integración en scripts.

```bash
python main.py
```

## Estructura del Proyecto

```
/
├── app.py                  # Servidor Web (Flask)
├── main.py                 # Punto de entrada CLI
├── requirements.txt        # Dependencias
├── .env                    # Variables de entorno
├── src/
│   ├── config/             # Gestión de configuración
│   ├── database/           # Lógica de BD (Modelos, Repositorios, Migraciones)
│   ├── models/             # Definiciones de objetos (ORM)
│   ├── services/           # Lógica de negocio
│   │   ├── ai_providers.py # Estrategias de IA (OpenAI/Gemini)
│   │   ├── scraper_primo.py# Web Scraping
│   │   └── ...
│   ├── gui.py              # Interfaz Gráfica
│   └── processor.py        # Núcleo de procesamiento lógico
├── templates/              # Plantillas HTML para la Web App
├── tests/                  # Tests unitarios y de integración
└── archivos/               # Carpeta por defecto para documentos
```

## Tecnologías

*   **Backend**: Python, Flask
*   **Base de Datos**: SQLite, SQLAlchemy (ORM)
*   **IA**: OpenAI API, Google Generative AI SDK
*   **Scraping**: Selenium WebDriver
*   **Procesamiento de Archivos**: PyMuPDF (PDF), Mammoth (Docx), Pandas
*   **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
