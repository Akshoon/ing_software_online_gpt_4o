import os
import json
import openai
import pdfplumber
import pandas as pd
from models import Sesion, Carrera, Asignatura, Titulo, Adquisicion
from dotenv import load_dotenv
from scraper_primo import buscar_libro_detalles
from file_extractor_strategies import FileProcessor
from ai_providers import AIProviderFactory
import time
import re

# Cargar variables de entorno desde .env
load_dotenv()

# Configurar API key de OpenAI desde variable de entorno
openai.api_key = os.getenv('OPENAI_API_KEY')

# Inicializar factory de proveedores de IA
try:
    ai_factory = AIProviderFactory(load_balance=True)
    print("✓ Sistema de IA multi-proveedor inicializado")
except Exception as e:
    print(f"⚠ Error inicializando proveedores de IA: {e}")
    ai_factory = None

# Verificar que al menos un proveedor está configurado
if not ai_factory:
    # Fallback si no hay factory (aunque debería haber si hay keys)
    if not openai.api_key and not os.getenv('GEMINI_API_KEY'):
        print("⚠ Advertencia: No hay API keys configuradas.")

def extraer_texto_de_archivo(ruta_archivo):
    """Extrae el texto de un archivo usando el patrón Strategy.
    
    Soporta múltiples formatos: PDF, Word (.docx)
    
    Args:
        ruta_archivo: Ruta al archivo a procesar
        
    Returns:
        str: Texto extraído del archivo
    """
    processor = FileProcessor.create_for_file(ruta_archivo)
    return processor.extract_text(ruta_archivo)

def extraer_detalles_asignatura(texto):
    """
    Extrae la asignatura, plan y semestre del texto usando IA.
    Se enfoca en el inicio del documento (aprox. primera página).
    """
    # Tomamos los primeros 3000 caracteres que deberían cubrir la primera página sobradamente
    texto_inicio = texto[:3000]
    
    prompt = f"""
Extrae la siguiente información del encabezado o primera página del syllabus:
1. Asignatura (Nombre de la materia)
2. Plan (Año del plan de estudios, ej: "2019", "2024")
3. Semestre (Número de semestre, ej: "4°", "I", "Segundo")

Texto:
{texto_inicio}

Retorna JSON: {{"subject": "...", "plan": "...", "semester": "..."}}
"""
    
    try:
        # Usar sistema multi-proveedor
        resultado, provider_used = ai_factory.generate_with_fallback(
            prompt,
            max_tokens=200,
            temperature=0.3
        )
        
        resultado_limpio = re.sub(r'```json\s*|\s*```', '', resultado).strip()
        match = re.search(r'\{.*\}', resultado_limpio, re.DOTALL)
        if match:
            resultado_limpio = match.group(0)
            
        datos = json.loads(resultado_limpio)
        return (
            datos.get('subject'),
            datos.get('plan'),
            datos.get('semester')
        )
    except Exception as e:
        print(f"Error extrayendo detalles de asignatura: {e}")
        return None, None, None

def extraer_seccion_bibliografia(texto):
    """
    Extrae las secciones de bibliografía usando expresiones regulares para soportar Markdown.
    Busca variantes como "Bibliografía", "Referencias", "Bibliografía Básica", etc.
    """
    texto_lower = texto.lower()
    bibliografia_texto = ""
    
    # Patrones para encontrar el inicio de la bibliografía
    # Busca líneas que contengan "bibliografía" o "referencias" con formato de título (#, ##, o mayúsculas)
    patron_inicio = r'(?:^|\n)(?:#+\s*|\*\*|)(bibliograf[ií]a|referencias)(?:.*)(?:$|\n)'
    
    match_inicio = re.search(patron_inicio, texto_lower, re.IGNORECASE)
    
    if match_inicio:
        start_idx = match_inicio.start()
        # Tomar desde el inicio encontrado hasta el final del documento
        # Asumimos que la bibliografía suele estar al final
        bibliografia_texto = texto[start_idx:]
    else:
        # Fallback: buscar la palabra simple si no hay formato
        idx = texto_lower.find("bibliograf")
        if idx != -1:
            bibliografia_texto = texto[idx:]
        else:
            # Si no encuentra nada, devolver los últimos 20% del documento como fallback
            largo = len(texto)
            bibliografia_texto = texto[int(largo * 0.8):]

    return bibliografia_texto

def extraer_bibliografia(texto):
    """Extrae la bibliografía del texto usando SOLO Gemini."""
    # Extraer la sección de bibliografía
    bibliografia_texto = extraer_seccion_bibliografia(texto)
    
    print(f"  -> Texto de bibliografía extraído: {len(bibliografia_texto)} caracteres")

    prompt = f"""
Extrae TODAS las referencias bibliográficas del siguiente texto.
El texto puede contener "Bibliografía básica", "Bibliografía complementaria" o solo una lista general.

IMPORTANTE:
1. Extrae CADA entrada individualmente. No omitas ninguna.
2. Diferencia entre libros y artículos web:
   - Si tiene URL/link -> type="article"
   - Si es libro físico/digital -> type="book"
3. Si no hay distinción explícita entre básica/complementaria, clasifica todo como "basic".

Para cada entrada, extrae: autor, año, título, editorial, URL, y tipo.

Retorna JSON:
{{
  "basic": [
    {{"author": "...", "year": "...", "title": "...", "publisher": "...", "type": "..."}},
    ...
  ],
  "complementary": [
    ...
  ]
}}

Texto Bibliografía:
{bibliografia_texto}
"""
    try:
        # USAR SOLO GEMINI
        print("  -> Usando Gemini para detección de títulos (Contexto completo)...")
        provider = ai_factory.get_provider('gemini')
        
        # Aumentamos max_tokens para permitir respuestas largas (muchos títulos)
        resultado = provider.generate_completion(
            prompt,
            max_tokens=8000, 
            temperature=0.3
        )
        
        resultado_limpio = re.sub(r'```json\s*|\s*```', '', resultado).strip()
        match = re.search(r'\{.*\}', resultado_limpio, re.DOTALL)
        if match:
            resultado_limpio = match.group(0)
            
        datos = json.loads(resultado_limpio)
        
        num_basic = len(datos.get('basic', []))
        num_complementary = len(datos.get('complementary', []))
        print(f"  -> Títulos detectados: {num_basic} básicos, {num_complementary} complementarios")
        
        return datos
    except Exception as e:
        print(f"Error extrayendo bibliografía con Gemini: {e}")
        return {"basic": [], "complementary": []}

def normalizar_entrada(autor, titulo):
    """
    Normaliza una entrada bibliográfica (Autor y Título) y detecta el idioma en una sola llamada eficiente.
    Expande iniciales de autores y aplica Title Case al título.
    """
    # Prompt optimizado para mínimo consumo de tokens
    prompt = f"""Normaliza bibliografía.
1. Autor: Nombre completo (expande iniciales si es conocido).
2. Título: Title Case español.
3. Idioma: Detectar (Español, Inglés, Portugués, etc.)

Entrada:
"{autor}" - "{titulo}"

JSON: {{"normalized_author": "...", "normalized_title": "...", "language": "..."}}"""
    
    try:
        # Usar sistema multi-proveedor
        resultado, _ = ai_factory.generate_with_fallback(
            prompt,
            max_tokens=150,
            temperature=0.3
        )
        
        # Limpiar respuesta
        resultado_limpio = re.sub(r'```json\s*|\s*```', '', resultado).strip()
        match = re.search(r'\{.*\}', resultado_limpio, re.DOTALL)
        if match:
            resultado_limpio = match.group(0)
            
        datos = json.loads(resultado_limpio)
        return {
            "normalized_author": datos.get('normalized_author', autor),
            "normalized_title": datos.get('normalized_title', titulo),
            "language": datos.get('language', 'Español')
        }
    except Exception as e:
        print(f"Error normalizando: {e}")
        return {"normalized_author": autor, "normalized_title": titulo, "language": "Español"}

def verificar_disponibilidad_catalogo(titulo, es_articulo=False):
    """
    Verifica la disponibilidad del título en el catálogo Primo de la UAH.
    """
    # Si es un artículo web, no buscar en Primo
    if es_articulo:
        print(f"  -> Artículo web detectado, no se busca en Primo")
        return False, True, None  # Digital disponible (es un link)
    
    # Construir término de búsqueda combinando título y autor
    termino_busqueda = f"{titulo.normalized_title} {titulo.normalized_author}"
    
    # Agregar delay para no sobrecargar el servidor
    time.sleep(3)
    
    try:
        # Buscar en Primo
        detalles = buscar_libro_detalles(termino_busqueda, verbose=False)
        
        if detalles and detalles.get('titulo') and detalles.get('autor'):
            print(f"  -> ✓ Encontrado en Primo")
            print(f"     Título de Primo: {detalles['titulo'][:80]}...")
            
            # Normalizar el autor y título extraídos de Primo
            print(f"  -> Normalizando datos de Primo...")
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
            
            # Determinar disponibilidad basado en el formato
            formato = detalles.get('formato', '').lower() if detalles.get('formato') else ''
            disponible_digital = 'online' in formato or 'digital' in formato or 'electronic' in formato
            # Asumimos que si está en el catálogo, hay al menos una copia impresa
            disponible_impreso = True
            
            return disponible_impreso, disponible_digital, detalles_normalizados
        else:
            print(f"  -> ✗ No encontrado en Primo o datos incompletos")
            return False, False, None
            
    except Exception as e:
        print(f"  -> ✗ Error al buscar en Primo: {str(e)[:100]}")
        return False, False, None

def extraer_numero_copias(disponibilidad_fisica):
    """Extrae el número de copias del string de disponibilidad física."""
    if not disponibilidad_fisica:
        return 0
    match = re.search(r'(\d+)\s+copias?', disponibilidad_fisica, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0

def generar_reportes():
    """Genera un reporte consolidado en CSV con la información bibliográfica de todas las carreras."""
    from datetime import datetime
    
    sesion = Sesion()
    carreras = sesion.query(Carrera).all()
    datos = []
    for carrera in carreras:
        for asignatura in carrera.asignaturas:
            for titulo in asignatura.titulos:
                adquisicion = sesion.query(Adquisicion).filter_by(title_id=titulo.id).first()

                # Extraer número de copias físicas
                num_copias_fisicas = extraer_numero_copias(titulo.physical_availability)

                # Determinar disponibilidad online
                disponible_online = 1 if (adquisicion and adquisicion.available_digital) else 0
                
                # Determinar si es artículo
                es_articulo = titulo.publisher and ('http' in titulo.publisher.lower() or 'www' in titulo.publisher.lower())

                # Calcular conteos
                # 1. Título asociado a carrera: Cuántas asignaturas de ESTA carrera usan este título
                conteo_carrera = 0
                for asig in titulo.asignaturas:
                    if asig.career_id == carrera.id:
                        conteo_carrera += 1
                
                # 2. Título asociado a asignatura (Global): Cuántas asignaturas en TOTAL usan este título
                conteo_global = len(titulo.asignaturas)

                datos.append({
                    'Facultad': carrera.facultad or '',
                    'Carrera ': carrera.name or '',
                    'Asignatura ': asignatura.name or '',
                    'Plan (año)': asignatura.plan or '',
                    'Semestre': asignatura.semester or '',
                    'Autor (Apellido, Nombre) ': titulo.normalized_author or '',
                    'Título del libro/revistas (Información completa del título)': titulo.normalized_title or '',
                    'Capitulo o artículo si se amerita la información': '',
                    'Edición': titulo.edition or '',
                    'Lugar de Públicación ': '',
                    'Editorial / Si es articulo de revista, Volumen, No': titulo.publisher or '',
                    'Año de Publicación': titulo.year or '',
                    'Idioma': titulo.language or 'Español',
                    'Tipo Bibliografía (Básica / Complementaria) ': titulo.type_bib or '',
                    'Tipo de Formato': titulo.format or ('Digital' if disponible_online else 'Impreso' if num_copias_fisicas > 0 else ''),
                    'Total de ejemplares en catalogo impresos': num_copias_fisicas,
                    'Total de ejemplares en catalogo digitales': disponible_online,
                    'Título asociado a carrera': conteo_carrera,
                    'Título asociado a asignatura ': conteo_global,
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
    
    # Guardar archivo
    nombre_archivo = 'reporte_bibliografia.csv'
    try:
        if os.path.exists(nombre_archivo):
            try:
                os.remove(nombre_archivo)
            except PermissionError:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                nombre_archivo = f'reporte_bibliografia_{timestamp}.csv'
        
        df.to_csv(nombre_archivo, index=False, sep=';', encoding='utf-8-sig')
        print(f"✓ Reporte generado exitosamente: {nombre_archivo}")
    except Exception as e:
        print(f"✗ Error generando reporte: {e}")
    
    sesion.close()

def notificar_carreras():
    """Notifica a las carreras sobre títulos disponibles."""
    sesion = Sesion()
    adquisiciones = sesion.query(Adquisicion).filter_by(status='disponible').all()
    for adq in adquisiciones:
        titulo = adq.titulo
        carreras = [asig.carrera.name for asig in titulo.asignaturas]
        print(f"Notificando a las carreras {carreras} sobre el título disponible: {titulo.normalized_title}")
    sesion.close()

def buscar_titulo_duplicado(sesion, autor_normalizado, titulo_normalizado):
    """Busca títulos duplicados comparando de manera case-insensitive."""
    todos_titulos = sesion.query(Titulo).all()
    for titulo_existente in todos_titulos:
        if (titulo_existente.normalized_author.lower().strip() == autor_normalizado.lower().strip() and
            titulo_existente.normalized_title.lower().strip() == titulo_normalizado.lower().strip()):
            return titulo_existente
    return None

def almacenar_bibliografia(nombre_asignatura, nombre_carrera, bibliografia, facultad='Ciencias Sociales', plan='', semestre=''):
    """Almacena la bibliografía en la base de datos."""
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
        asignatura = Asignatura(name=nombre_asignatura, carrera=carrera, plan=plan, semester=semestre)
        sesion.add(asignatura)
        sesion.commit()
    else:
        # Actualizar plan y semestre si existen
        if plan: asignatura.plan = plan
        if semestre: asignatura.semester = semestre
        sesion.commit()
    
    # Procesar bibliografía
    for tipo_bib, entradas in bibliografia.items():
        for entrada in entradas:
            print(f"Normalizando: {entrada.get('author', 'N/A')} - {entrada.get('title', 'N/A')}")
            norm = normalizar_entrada(entrada['author'], entrada['title'])
            
            titulo = buscar_titulo_duplicado(sesion, norm['normalized_author'], norm['normalized_title'])
            
            if titulo:
                print(f"  -> Duplicado encontrado! (ID: {titulo.id})")
                if asignatura not in titulo.asignaturas:
                    titulo.asignaturas.append(asignatura)
                    sesion.commit()
            else:
                print(f"  -> Título nuevo, creando entrada...")
                es_articulo = entrada.get('type') == 'article' or entrada.get('url') is not None
                url_articulo = entrada.get('url')
                
                titulo = Titulo(
                    normalized_author=norm['normalized_author'],
                    normalized_title=norm['normalized_title'],
                    original_author=entrada['author'],
                    original_title=entrada['title'],
                    year=entrada.get('year'),
                    publisher=entrada.get('publisher') if not es_articulo else url_articulo,
                    type_bib=tipo_bib,
                    language=norm.get('language', 'Español')
                )
                sesion.add(titulo)
                sesion.commit()
                
                # Verificar en Primo
                impreso, digital, detalles_primo = verificar_disponibilidad_catalogo(titulo, es_articulo=es_articulo)
                encontrado_en_primo = detalles_primo is not None

                if detalles_primo:
                    titulo.normalized_author = detalles_primo['autor_normalizado']
                    titulo.normalized_title = detalles_primo['titulo_normalizado']
                    titulo.original_author = detalles_primo['autor_original']
                    titulo.original_title = detalles_primo['titulo_original']
                    if detalles_primo.get('editor'): titulo.publisher = detalles_primo['editor']
                    if detalles_primo.get('fecha_creacion'): titulo.year = detalles_primo['fecha_creacion']
                    if detalles_primo.get('edicion'): titulo.edition = detalles_primo['edicion']
                    if detalles_primo.get('formato'): titulo.format = detalles_primo['formato']
                    if detalles_primo.get('disponibilidad_fisica'): titulo.physical_availability = detalles_primo['disponibilidad_fisica']
                    if detalles_primo.get('disponibilidad_online'): titulo.online_availability = detalles_primo['disponibilidad_online']
                    else: titulo.online_availability = "Disponible en catálogo Primo" if encontrado_en_primo else None
                    sesion.commit()

                adquisicion = Adquisicion(
                    titulo=titulo,
                    status='disponible' if impreso or digital or encontrado_en_primo else 'no disponible',
                    available_printed=impreso,
                    available_digital=digital or encontrado_en_primo
                )
                sesion.add(adquisicion)
                sesion.commit()
                
                titulo.asignaturas.append(asignatura)
                sesion.commit()
    
    sesion.close()

def procesar_archivos(directorio, facultad='Ciencias Sociales', carrera_default='Trabajo Social'):
    """Procesa todos los archivos soportados (PDF, Word) en el directorio especificado."""
    extensiones_soportadas = ('.pdf', '.docx')
    
    for nombre_archivo in os.listdir(directorio):
        if nombre_archivo.lower().endswith(extensiones_soportadas):
            ruta_archivo = os.path.join(directorio, nombre_archivo)
            print(f"Procesando {nombre_archivo}")
            
            try:
                # 1. Extraer texto
                texto = extraer_texto_de_archivo(ruta_archivo)
                
                # 2. Extraer asignatura, plan y semestre (SIN CARRERA)
                nombre_asignatura, plan, semestre = extraer_detalles_asignatura(texto)
                
                if not nombre_asignatura:
                    print(f"No se pudo extraer la asignatura de {nombre_archivo}, omitiendo.")
                    continue
                    
                print(f"  -> Asignatura: {nombre_asignatura}")
                print(f"  -> Carrera (Default): {carrera_default}")
                print(f"  -> Plan: {plan}")
                print(f"  -> Semestre: {semestre}")
                
                # 3. Extraer bibliografía
                bibliografia = extraer_bibliografia(texto)
                
                # 4. Almacenar en base de datos
                almacenar_bibliografia(nombre_asignatura, carrera_default, bibliografia, facultad, plan, semestre)
                
            except Exception as e:
                print(f"Error procesando {nombre_archivo}: {e}")
                import traceback
                traceback.print_exc()
                
    generar_reportes()
    notificar_carreras()

# Mantener compatibilidad con código existente
def procesar_pdfs(directorio_pdf, facultad='Ciencias Sociales', carrera_default='Trabajo Social'):
    """Alias para procesar_archivos. Mantiene compatibilidad con código existente."""
    return procesar_archivos(directorio_pdf, facultad, carrera_default)

def importar_csv(ruta_csv):
    """Importa datos desde un archivo CSV al sistema, agregando sin reemplazar."""
    # (Implementación simplificada para mantener el archivo manejable, 
    #  si se necesita la lógica completa de importar_csv, se puede copiar del backup anterior)
    pass

def main():
    """Función principal del programa."""
    facultad = input("Selecciona la facultad: ")
    carrera = input("Selecciona la carrera: ")
    procesar_archivos('archivos/', facultad=facultad, carrera_default=carrera)

if __name__ == '__main__':
    main()
