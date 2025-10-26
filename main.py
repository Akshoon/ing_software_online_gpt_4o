import os
import json
import openai
import pdfplumber
import pandas as pd
from models import Sesion, Carrera, Asignatura, Titulo, Adquisicion
from dotenv import load_dotenv
from scraper_primo import buscar_libro_detalles
import time

# Cargar variables de entorno desde .env
load_dotenv()

# Configurar API key de OpenAI desde variable de entorno
openai.api_key = os.getenv('OPENAI_API_KEY')

# Verificar que la API key está configurada
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY no está configurada. Por favor, crea un archivo .env con tu clave de API.")

def extraer_texto_de_pdf(ruta_pdf):
    """Extrae el texto de un archivo PDF."""
    with pdfplumber.open(ruta_pdf) as pdf:
        texto = ''
        for pagina in pdf.pages:
            texto += pagina.extract_text() + '\n'
    return texto

def extraer_asignatura_y_carrera(texto, facultad_default='Ciencias Sociales', carrera_default='Trabajo Social'):
    """Extrae el nombre de la asignatura y carrera del texto del PDF."""
    prompt = f"""
Extrae el nombre de la asignatura y la carrera del siguiente texto de PDF.
La asignatura usualmente está bajo "Nombre de la Asignatura:" o similar.
La carrera esta situada en el encabezado del archivo, esta como una imagen como texto, busca palabras como "Grado en", "Diplomatura en", "Doctorado en", etc.

Retorna en JSON: {{"subject": "Nombre de la Asignatura", "career": "Nombre de la Carrera"}}
Texto:
{texto[:1000]}  # Primeros 1000 caracteres
"""
    respuesta = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    resultado = respuesta['choices'][0]['message']['content']
    try:
        datos = json.loads(resultado)
        subject = datos.get('subject')
        career = datos.get('career', carrera_default)
        return subject, career
    except:
        return None, carrera_default

def extraer_seccion_bibliografia(texto):
    """Extrae solo las secciones de bibliografía básica y complementaria del texto completo."""
    texto_lower = texto.lower()
    bibliografia_texto = ""

    # Buscar "Bibliografía básica"
    idx_basica = texto_lower.find("bibliografía básica")
    if idx_basica != -1:
        # Tomar desde "Bibliografía básica" hasta el final o hasta "Bibliografía complementaria"
        idx_complementaria = texto_lower.find("bibliografía complementaria", idx_basica)
        if idx_complementaria != -1:
            bibliografia_texto += texto[idx_basica:idx_complementaria]
        else:
            bibliografia_texto += texto[idx_basica:]

    # Buscar "Bibliografía complementaria"
    idx_complementaria = texto_lower.find("bibliografía complementaria")
    if idx_complementaria != -1:
        bibliografia_texto += texto[idx_complementaria:]

    # Si no se encontró ninguna, devolver el texto completo (fallback)
    if not bibliografia_texto:
        bibliografia_texto = texto

    return bibliografia_texto

def extraer_bibliografia(texto):
    """Extrae la bibliografía del texto del PDF."""
    # Extraer solo las secciones relevantes de bibliografía
    bibliografia_texto = extraer_seccion_bibliografia(texto)

    prompt = f"""
Extrae la bibliografía del siguiente texto. La bibliografía está dividida en "Bibliografía básica" y "Bibliografía complementaria".

IMPORTANTE: Diferencia entre libros y artículos web:
- Si tiene URL/link (http://, https://, www.) → es un artículo web, marca type="article"
- Si tiene editorial, ISBN, o es un libro físico → marca type="book"

Para cada entrada, extrae: autor, año, título, editorial (si aplica), URL (si aplica), y tipo.

Retorna en formato JSON como:
{{
  "basic": [
    {{"author": "Nombre del Autor", "year": "2020", "title": "Título", "publisher": "Editorial", "type": "book"}},
    {{"author": "Autor", "year": "2011", "title": "Título del artículo", "url": "http://...", "type": "article"}}
  ],
  "complementary": [
    ...
  ]
}}

Texto:
{bibliografia_texto}
"""
    respuesta = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    resultado = respuesta['choices'][0]['message']['content']
    try:
        return json.loads(resultado)
    except:
        return {"basic": [], "complementary": []}

def buscar_nombre_completo_autor(autor):
    """
    Busca el nombre completo del autor en internet si está abreviado.
    Usa OpenAI para buscar información del autor.
    """
    # Detectar si el nombre tiene iniciales (ej: "D. Martuccelli", "J.K. Rowling")
    import re
    tiene_iniciales = bool(re.search(r'\b[A-Z]\.\s', autor))
    
    if not tiene_iniciales:
        return autor  # Ya tiene nombre completo
    
    prompt = f"""
El siguiente autor tiene un nombre abreviado: "{autor}"

Por favor, busca en tu conocimiento el nombre completo de este autor académico.
Si es un autor conocido en ciencias sociales, sociología, o trabajo social, proporciona su nombre completo.

Ejemplos:
- "D. Martuccelli" → "Danilo Martuccelli"
- "J.K. Rowling" → "Joanne Kathleen Rowling"
- "P. Bourdieu" → "Pierre Bourdieu"

Retorna SOLO el nombre completo en formato JSON: {{"full_name": "Nombre Completo"}}

Si no puedes encontrar el nombre completo con certeza, retorna el nombre original.
"""
    
    try:
        respuesta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        resultado = respuesta['choices'][0]['message']['content']
        datos = json.loads(resultado)
        nombre_completo = datos.get('full_name', autor)
        return nombre_completo if nombre_completo else autor
    except:
        return autor

def normalizar_entrada(autor, titulo):
    """
    Normaliza una entrada bibliográfica:
    - Expande nombres abreviados de autores buscando en internet
    - Normaliza el formato del nombre (Nombre Apellido)
    - Normaliza el título con capitalización estándar
    """
    # Primero, buscar el nombre completo si está abreviado
    autor_completo = buscar_nombre_completo_autor(autor)
    
    prompt = f"""
Normaliza la siguiente entrada bibliográfica:
Autor: {autor_completo}
Título: {titulo}

INSTRUCCIONES IMPORTANTES:
1. Para el autor:
   - Usa el formato: "Nombre Apellido" (ej: "Danilo Martuccelli", no "Martuccelli, D.")
   - Si hay múltiples autores, sepáralos con comas
   - Asegúrate de usar el nombre completo, no iniciales
   - Estandariza el formato (primera letra mayúscula en cada nombre)

2. Para el título:
   - Usa capitalización estándar (Title Case en español)
   - Primera palabra siempre con mayúscula
   - Palabras importantes con mayúscula inicial
   - Artículos, preposiciones y conjunciones en minúscula (excepto al inicio)
   - Elimina espacios extras y caracteres especiales innecesarios

Ejemplos:
- "D. Martuccelli" → "Danilo Martuccelli"
- "TRANSFORMACIONES DE LA ACCIÓN PÚBLICA" → "Transformaciones de la Acción Pública"
- "el nuevo gobierno de los individuos" → "El Nuevo Gobierno de los Individuos"

Retorna en JSON: {{"normalized_author": "Autor Normalizado", "normalized_title": "Título Normalizado"}}
"""
    
    try:
        respuesta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        resultado = respuesta['choices'][0]['message']['content']
        datos = json.loads(resultado)
        return {
            "normalized_author": datos.get('normalized_author', autor_completo),
            "normalized_title": datos.get('normalized_title', titulo)
        }
    except Exception as e:
        print(f"Error normalizando entrada: {e}")
        return {"normalized_author": autor_completo, "normalized_title": titulo}

def verificar_disponibilidad_catalogo(titulo, es_articulo=False):
    """
    Verifica la disponibilidad del título en el catálogo Primo de la UAH.
    Busca el libro por título y autor, y extrae información real del catálogo.
    Normaliza los datos extraídos de Primo.
    
    Args:
        titulo: Objeto Titulo de la base de datos
        es_articulo: Si es True, no busca en Primo (es un artículo web)
    
    Returns:
        tuple: (disponible_impreso, disponible_digital, detalles_primo_normalizados)
               donde detalles_primo_normalizados incluye autor y título normalizados de Primo
    """
    # Si es un artículo web, no buscar en Primo
    if es_articulo:
        print(f"  → Artículo web detectado, no se busca en Primo")
        return False, True, None  # Digital disponible (es un link)
    
    print(f"  → Buscando en catálogo Primo: {titulo.normalized_title}")
    
    # Construir término de búsqueda combinando título y autor
    termino_busqueda = f"{titulo.normalized_title} {titulo.normalized_author}"
    
    # Agregar delay para no sobrecargar el servidor
    time.sleep(3)
    
    try:
        # Buscar en Primo
        detalles = buscar_libro_detalles(termino_busqueda, verbose=False)
        
        if detalles and detalles.get('titulo') and detalles.get('autor'):
            print(f"  → ✓ Encontrado en Primo")
            print(f"     Título de Primo: {detalles['titulo'][:80]}...")
            print(f"     Autor de Primo: {detalles['autor']}")
            
            # Normalizar el autor y título extraídos de Primo
            print(f"  → Normalizando datos de Primo...")
            datos_normalizados = normalizar_entrada(detalles['autor'], detalles['titulo'])
            
            # Crear diccionario con todos los detalles normalizados
            detalles_normalizados = {
                'autor_normalizado': datos_normalizados['normalized_author'],
                'titulo_normalizado': datos_normalizados['normalized_title'],
                'autor_original': detalles['autor'],
                'titulo_original': detalles['titulo'],
                'editor': detalles.get('editor'),
                'fecha_creacion': detalles.get('fecha_creacion'),
                'edicion': detalles.get('edicion'),
                'formato': detalles.get('formato'),
                'disponibilidad_fisica': detalles.get('disponibilidad_fisica'),
                'disponibilidad_online': detalles.get('disponibilidad_online')
            }
            
            print(f"     Autor normalizado: {detalles_normalizados['autor_normalizado']}")
            print(f"     Título normalizado: {detalles_normalizados['titulo_normalizado'][:80]}...")
            
            # Determinar disponibilidad basado en el formato
            formato = detalles.get('formato', '').lower() if detalles.get('formato') else ''
            disponible_digital = 'online' in formato or 'digital' in formato or 'electronic' in formato
            # Asumimos que si está en el catálogo, hay al menos una copia impresa
            disponible_impreso = True
            
            return disponible_impreso, disponible_digital, detalles_normalizados
        else:
            print(f"  → ✗ No encontrado en Primo o datos incompletos")
            return False, False, None
            
    except Exception as e:
        print(f"  → ✗ Error al buscar en Primo: {str(e)[:100]}")
        # No imprimir traceback completo para mantener el log limpio
        return False, False, None

def detectar_idioma(titulo):
    """
    Detecta el idioma del título usando OpenAI.
    Retorna códigos ISO de 3 letras para el idioma detectado.
    """
    if not titulo or titulo.strip() == '':
        return ''

    prompt = f"""
Analiza el siguiente título y determina el idioma principal.

Título: "{titulo}"

INSTRUCCIONES:
- Retorna el código ISO de 3 letras del idioma principal del título
- Si está en inglés: ENG
- Si está en español: SPA
- Si está en francés: FRA
- Si está en alemán: GER
- Si está en italiano: ITA
- Si está en portugués: POR
- Si está en catalán: CAT
- Si está en gallego: GLG
- Si está en euskera: EUS
- Si no puedes determinar con certeza o es multilingüe: OTR (otro)
- Si el título parece ser un acrónimo o código sin idioma claro: N/A

Ejemplos:
- "The Interpretation of Cultures" → ENG
- "La Interpretación de las Culturas" → SPA
- "Transformaciones de la Acción Pública" → SPA
- "Social Work and Social Policy" → ENG
- "La Sociologie Française Contemporaine" → FRA
- "Die Gesellschaft der Gesellschaft" → GER
- "Il Capitale Sociale" → ITA
- "A Sociedade Portuguesa" → POR

Retorna SOLO el código de idioma sin explicación adicional.
"""

    try:
        respuesta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10
        )
        resultado = respuesta['choices'][0]['message']['content'].strip().upper()
        # Validar que sea un código de idioma válido
        idiomas_validos = ['ENG', 'SPA', 'FRA', 'GER', 'ITA', 'POR', 'CAT', 'GLG', 'EUS', 'OTR', 'N/A']
        if resultado in idiomas_validos:
            return resultado
        else:
            return 'OTR'  # Otro idioma si no está en la lista
    except Exception as e:
        print(f"Error detectando idioma para '{titulo}': {e}")
        return 'OTR'

def extraer_numero_copias(disponibilidad_fisica):
    """
    Extrae el número de copias del string de disponibilidad física.
    Ejemplo: "(16 copias, 16 disponible, 0 solicitudes)" -> 16
    """
    if not disponibilidad_fisica:
        return 0

    import re
    # Buscar patrón: "(\d+) copias"
    match = re.search(r'(\d+)\s+copias?', disponibilidad_fisica, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0

def procesar_disponibilidad_online(disponibilidad_str):
    """
    Convierte la disponibilidad online a formato binario.
    Solo retorna 1 si el texto es exactamente "Disponible en línea".

    Args:
        disponibilidad_str (str): String con disponibilidad online

    Returns:
        int: 1 si está disponible online, 0 si no
    """
    if not disponibilidad_str:
        return 0

    # Solo marcar como disponible si dice exactamente "Disponible en línea"
    if disponibilidad_str.strip() == "Disponible en línea":
        return 1

    return 0

def generar_reportes():
    """Genera un reporte consolidado en CSV con la información bibliográfica de todas las carreras."""
    from datetime import datetime
    import time

    sesion = Sesion()
    carreras = sesion.query(Carrera).all()
    datos = []
    for carrera in carreras:
        for asignatura in carrera.asignaturas:
            for titulo in asignatura.titulos:
                adquisicion = sesion.query(Adquisicion).filter_by(title_id=titulo.id).first()

                # Extraer número de copias físicas
                num_copias_fisicas = extraer_numero_copias(titulo.physical_availability)

                # Determinar disponibilidad online:
                # Usar el campo available_digital de la adquisición para determinar si está disponible online
                disponible_online = 1 if adquisicion.available_digital else 0
                
                # Determinar si es artículo (basado en si publisher contiene URL)
                es_articulo = titulo.publisher and ('http' in titulo.publisher.lower() or 'www' in titulo.publisher.lower())

                datos.append({
                    'Facultad': carrera.facultad or '',
                    'Carrera ': carrera.name or '',
                    'Asignatura ': asignatura.name or '',
                    'Plan (año)': '',
                    'Semestre': '',
                    'Autor (Apellido, Nombre) ': titulo.normalized_author or '',
                    'Título del libro/revistas (Información completa del título)': titulo.normalized_title or '',
                    'Capitulo o artículo si se amerita la información': '',
                    'Edición': titulo.edition or '',
                    'Lugar de Públicación ': '',
                    'Editorial / Si es articulo de revista, Volumen, No': titulo.publisher or '',
                    'Año de Publicación': titulo.year or '',
                    'Idioma': detectar_idioma(titulo.normalized_title) if titulo.normalized_title else '',
                    'Tipo Bibliografía (Básica / Complementaria) ': titulo.type_bib or '',
                    'Tipo de Formato': titulo.format or '',
                    'Total de ejemplares en catalogo impresos': num_copias_fisicas,
                    'Total de ejemplares en catalogo digitales': disponible_online,
                    'Título asociado a carrera': '',
                    'Título asociado a asignatura ': '',
                    'Basica ': 1 if (titulo.type_bib and 'basic' in titulo.type_bib.lower()) else 0,
                    'Complementaria ': 1 if (titulo.type_bib and 'complementary' in titulo.type_bib.lower()) else 0,
                    'Colección ': '',
                    'Número de pédido': '',
                    'Plataforma de bibliografía': '',
                    'Fuente del recurso ': '',
                    'link': titulo.publisher if es_articulo else '',
                    'Procedencia de información': '',
                    'Notas ': '',
                    'Títulos Solicitados': 1,
                    'Títulos en Biblioteca': 1 if (adquisicion and (adquisicion.available_printed or adquisicion.available_digital)) else 0
                })
    df = pd.DataFrame(datos)
    
    # Intentar guardar el archivo con manejo de errores
    nombre_archivo = 'reporte_bibliografia.csv'
    intentos = 0
    max_intentos = 3
    
    while intentos < max_intentos:
        try:
            # Intentar eliminar el archivo existente si está presente
            if os.path.exists(nombre_archivo):
                try:
                    os.remove(nombre_archivo)
                    print(f"Archivo existente '{nombre_archivo}' eliminado.")
                except PermissionError:
                    # Si no se puede eliminar, crear uno nuevo con timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    nombre_archivo = f'reporte_bibliografia_{timestamp}.csv'
                    print(f"Archivo bloqueado. Creando nuevo archivo: {nombre_archivo}")
            
            # Guardar como CSV con separador de punto y coma (;) como en el archivo original
            df.to_csv(nombre_archivo, index=False, sep=';', encoding='utf-8-sig')
            print(f"✓ Reporte generado exitosamente: {nombre_archivo} con {len(datos)} registros")
            break
            
        except PermissionError as e:
            intentos += 1
            if intentos < max_intentos:
                print(f"Error de permisos al escribir el archivo. Reintentando en 2 segundos... (Intento {intentos}/{max_intentos})")
                time.sleep(2)
                # Generar nuevo nombre con timestamp para el siguiente intento
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                nombre_archivo = f'reporte_bibliografia_{timestamp}.csv'
            else:
                print(f"✗ Error: No se pudo guardar el archivo después de {max_intentos} intentos.")
                print(f"  Por favor, cierra cualquier programa que tenga abierto 'reporte_bibliografia.csv' y ejecuta el programa nuevamente.")
                raise
        except Exception as e:
            print(f"✗ Error inesperado al generar el reporte: {e}")
            raise
    
    sesion.close()

def notificar_carreras():
    """Notifica a las carreras sobre títulos disponibles."""
    sesion = Sesion()
    adquisiciones = sesion.query(Adquisicion).filter_by(status='disponible').all()
    for adq in adquisiciones:
        titulo = adq.titulo
        carreras = [asig.carrera.name for asig in titulo.asignaturas]
        print(f"Notificando a las carreras {carreras} sobre el título disponible: {titulo.normalized_title} de {titulo.normalized_author}")
    sesion.close()

def buscar_titulo_duplicado(sesion, autor_normalizado, titulo_normalizado):
    """
    Busca títulos duplicados comparando de manera case-insensitive.
    Esto ayuda a detectar duplicados con diferentes mayúsculas.
    """
    from sqlalchemy import func
    
    # Buscar títulos con autor y título similares (ignorando mayúsculas)
    todos_titulos = sesion.query(Titulo).all()
    
    for titulo_existente in todos_titulos:
        # Comparar ignorando mayúsculas y espacios extras
        if (titulo_existente.normalized_author.lower().strip() == autor_normalizado.lower().strip() and
            titulo_existente.normalized_title.lower().strip() == titulo_normalizado.lower().strip()):
            return titulo_existente
    
    return None

def almacenar_bibliografia(nombre_asignatura, nombre_carrera, bibliografia, facultad='Ciencias Sociales'):
    """
    Almacena la bibliografía en la base de datos.
    Detecta y previene duplicados comparando autores y títulos normalizados.
    """
    sesion = Sesion()
    # Obtener o crear carrera
    carrera = sesion.query(Carrera).filter_by(name=nombre_carrera).first()
    if not carrera:
        carrera = Carrera(name=nombre_carrera, facultad=facultad)
        sesion.add(carrera)
        sesion.commit()
    # Obtener o crear asignatura
    asignatura = sesion.query(Asignatura).filter_by(name=nombre_asignatura, career_id=carrera.id).first()
    if not asignatura:
        asignatura = Asignatura(name=nombre_asignatura, carrera=carrera)
        sesion.add(asignatura)
        sesion.commit()
    
    # Para cada tipo de bibliografía
    for tipo_bib, entradas in bibliografia.items():
        for entrada in entradas:
            # Normalizar
            print(f"Normalizando: {entrada.get('author', 'N/A')} - {entrada.get('title', 'N/A')}")
            norm = normalizar_entrada(entrada['author'], entrada['title'])
            print(f"  → Normalizado: {norm['normalized_author']} - {norm['normalized_title']}")
            
            # Buscar duplicados de manera robusta (case-insensitive)
            titulo = buscar_titulo_duplicado(sesion, norm['normalized_author'], norm['normalized_title'])
            
            if titulo:
                print(f"  → Duplicado encontrado! Usando título existente (ID: {titulo.id})")
                # Verificar si ya está asociado con esta asignatura
                if asignatura not in titulo.asignaturas:
                    # Asociar con asignatura
                    titulo.asignaturas.append(asignatura)
                    sesion.commit()
                    print(f"  → Asociado con asignatura: {nombre_asignatura}")
                else:
                    print(f"  → Ya estaba asociado con esta asignatura")
            else:
                print(f"  → Título nuevo, creando entrada...")
                
                # Detectar si es un artículo web (tiene URL)
                es_articulo = entrada.get('type') == 'article' or entrada.get('url') is not None
                url_articulo = entrada.get('url')
                
                if es_articulo:
                    print(f"  → Detectado como artículo web: {url_articulo}")
                
                titulo = Titulo(
                    normalized_author=norm['normalized_author'],
                    normalized_title=norm['normalized_title'],
                    original_author=entrada['author'],
                    original_title=entrada['title'],
                    year=entrada.get('year'),
                    publisher=entrada.get('publisher') if not es_articulo else url_articulo,
                    type_bib=tipo_bib
                )
                sesion.add(titulo)
                sesion.commit()
                
                # Verificar catálogo y obtener detalles normalizados de Primo
                # Solo buscar en Primo si NO es un artículo web
                impreso, digital, detalles_primo = verificar_disponibilidad_catalogo(titulo, es_articulo=es_articulo)

                # Si se encontró en Primo, significa que está disponible online
                encontrado_en_primo = detalles_primo is not None

                # Actualizar información del título con datos normalizados de Primo
                if detalles_primo:
                    # IMPORTANTE: Usar autor y título normalizados de Primo
                    titulo.normalized_author = detalles_primo['autor_normalizado']
                    titulo.normalized_title = detalles_primo['titulo_normalizado']
                    titulo.original_author = detalles_primo['autor_original']
                    titulo.original_title = detalles_primo['titulo_original']

                    # Actualizar otros campos
                    if detalles_primo.get('editor'):
                        titulo.publisher = detalles_primo['editor']
                    if detalles_primo.get('fecha_creacion'):
                        titulo.year = detalles_primo['fecha_creacion']

                    # Guardar información adicional de edición y formato
                    if detalles_primo.get('edicion'):
                        titulo.edition = detalles_primo['edicion']
                    if detalles_primo.get('formato'):
                        titulo.format = detalles_primo['formato']

                    # Guardar información de disponibilidad física
                    if detalles_primo.get('disponibilidad_fisica'):
                        titulo.physical_availability = detalles_primo['disponibilidad_fisica']

                    # Usar la información real de disponibilidad online de Primo
                    if detalles_primo.get('disponibilidad_online'):
                        titulo.online_availability = detalles_primo['disponibilidad_online']
                    else:
                        titulo.online_availability = "Disponible en catálogo Primo" if encontrado_en_primo else None

                    sesion.commit()
                    print(f"  → Título actualizado con datos de Primo")
                else:
                    # No se encontró en Primo
                    titulo.online_availability = None
                    print(f"  → No encontrado en Primo - no disponible online")

                adquisicion = Adquisicion(
                    titulo=titulo,
                    status='disponible' if impreso or digital or encontrado_en_primo else 'no disponible',
                    available_printed=impreso,
                    available_digital=digital or encontrado_en_primo  # Si está en Primo, está disponible digitalmente
                )
                sesion.add(adquisicion)
                sesion.commit()
                
                # Asociar con asignatura
                titulo.asignaturas.append(asignatura)
                sesion.commit()
                print(f"  → Título creado (ID: {titulo.id}) y asociado con asignatura")
    
    sesion.close()

def procesar_pdfs(directorio_pdf, facultad='Ciencias Sociales', carrera_default='Trabajo Social'):
    """Procesa todos los archivos PDF en el directorio especificado."""
    for nombre_archivo in os.listdir(directorio_pdf):
        if nombre_archivo.endswith('.pdf'):
            ruta_pdf = os.path.join(directorio_pdf, nombre_archivo)
            print(f"Procesando {nombre_archivo}")
            texto = extraer_texto_de_pdf(ruta_pdf)
            asignatura, _ = extraer_asignatura_y_carrera(texto, facultad, carrera_default)
            if asignatura is None:
                print(f"No se pudo extraer la asignatura de {nombre_archivo}, omitiendo.")
                continue
            bibliografia = extraer_bibliografia(texto)
            # Usar la carrera especificada por el usuario en lugar de la extraída del PDF
            almacenar_bibliografia(asignatura, carrera_default, bibliografia, facultad)
    generar_reportes()
    notificar_carreras()

def importar_csv(ruta_csv):
    """Importa datos desde un archivo CSV al sistema, agregando sin reemplazar."""
    try:
        df = pd.read_csv(ruta_csv, sep=';', encoding='utf-8-sig')
        print(f"Importando {len(df)} registros desde {ruta_csv}")
        sesion = Sesion()
        for _, row in df.iterrows():
            # Obtener o crear carrera
            carrera_name = row.get('Carrera ', '').strip()
            facultad = row.get('Facultad', 'Ciencias Sociales').strip()
            if carrera_name:
                carrera = sesion.query(Carrera).filter_by(name=carrera_name).first()
                if not carrera:
                    carrera = Carrera(name=carrera_name, facultad=facultad)
                    sesion.add(carrera)
                    sesion.commit()
                    print(f"Carrera creada: {carrera_name}")

            # Obtener o crear asignatura
            asignatura_name = row.get('Asignatura ', '').strip()
            if asignatura_name and carrera:
                asignatura = sesion.query(Asignatura).filter_by(name=asignatura_name, career_id=carrera.id).first()
                if not asignatura:
                    asignatura = Asignatura(name=asignatura_name, carrera=carrera)
                    sesion.add(asignatura)
                    sesion.commit()
                    print(f"Asignatura creada: {asignatura_name}")

            # Crear título si no existe
            autor = row.get('Autor (Apellido, Nombre) ', '').strip()
            titulo_texto = row.get('Título del libro/revistas (Información completa del título)', '').strip()
            if autor and titulo_texto:
                # Normalizar
                norm = normalizar_entrada(autor, titulo_texto)
                titulo_existente = buscar_titulo_duplicado(sesion, norm['normalized_author'], norm['normalized_title'])
                if not titulo_existente:
                    # Determinar tipo de bibliografía
                    type_bib = 'basic' if row.get('Basica ', 0) == 1 else 'complementary' if row.get('Complementaria ', 0) == 1 else 'basic'
                    # Detectar si es artículo
                    link = row.get('link', '').strip()
                    es_articulo = bool(link and ('http' in link.lower() or 'www' in link.lower()))
                    publisher = link if es_articulo else row.get('Editorial / Si es articulo de revista, Volumen, No', '').strip()

                    titulo = Titulo(
                        normalized_author=norm['normalized_author'],
                        normalized_title=norm['normalized_title'],
                        original_author=autor,
                        original_title=titulo_texto,
                        year=row.get('Año de Publicación', ''),
                        publisher=publisher,
                        type_bib=type_bib,
                        edition=row.get('Edición', ''),
                        format=row.get('Tipo de Formato', ''),
                        physical_availability=f"{row.get('Total de ejemplares en catalogo impresos', 0)} copias" if row.get('Total de ejemplares en catalogo impresos', 0) > 0 else None,
                        online_availability="Disponible en línea" if row.get('Total de ejemplares en catalogo digitales', 0) > 0 else None
                    )
                    sesion.add(titulo)
                    sesion.commit()

                    # Crear adquisición
                    available_printed = row.get('Total de ejemplares en catalogo impresos', 0) > 0
                    available_digital = row.get('Total de ejemplares en catalogo digitales', 0) > 0
                    adquisicion = Adquisicion(
                        titulo=titulo,
                        status='disponible' if available_printed or available_digital else 'no disponible',
                        available_printed=available_printed,
                        available_digital=available_digital
                    )
                    sesion.add(adquisicion)
                    sesion.commit()

                    # Asociar con asignatura
                    if asignatura:
                        titulo.asignaturas.append(asignatura)
                        sesion.commit()
                        print(f"Título creado y asociado: {norm['normalized_title']}")
                    else:
                        print(f"Título creado pero no asociado: {norm['normalized_title']}")
                else:
                    print(f"Título duplicado omitido: {norm['normalized_title']}")
        sesion.close()
        print("Importación completada.")
    except Exception as e:
        print(f"Error importando CSV: {e}")
        raise

def main():
    """Función principal del programa."""
    facultad = input("Selecciona la facultad: ")
    carrera = input("Selecciona la carrera: ")
    procesar_pdfs('archivos/', facultad=facultad, carrera_default=carrera)

if __name__ == '__main__':
    main()
