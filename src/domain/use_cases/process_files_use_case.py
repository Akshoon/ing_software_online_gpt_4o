"""
Caso de uso: ProcessFilesUseCase
Orquesta todo el flujo de procesamiento de archivos de syllabus:
  1. Extrae texto del archivo
  2. Detecta asignatura/plan/semestre con IA
  3. Extrae bibliografía con IA
  4. Normaliza entradas con IA
  5. Verifica disponibilidad en catálogo
  6. Persiste datos en repositorios

Solo depende de puertos (interfaces), no de implementaciones concretas.
"""
import os
import json
import re
import time
from typing import List, Optional

from src.domain.entities.bibliography import BibliographyEntry
from src.domain.entities.title import Title
from src.domain.entities.acquisition import Acquisition
from src.domain.ports.repository_ports import (
    CarreraRepositoryPort,
    AsignaturaRepositoryPort,
    TituloRepositoryPort,
    AdquisicionRepositoryPort,
)
from src.domain.ports.ai_port import AIProviderPort
from src.domain.ports.catalog_port import CatalogSearchPort
from src.domain.ports.file_extractor_port import FileExtractorPort


class ProcessFilesUseCase:
    """
    Caso de uso principal: procesa todos los archivos soportados de un directorio.

    Recibe todos sus colaboradores por inyección de dependencias (puertos).
    """

    SUPPORTED_EXTENSIONS = ('.pdf', '.docx')

    def __init__(
        self,
        file_extractor: FileExtractorPort,
        ai_provider: AIProviderPort,
        catalog: CatalogSearchPort,
        carrera_repo: CarreraRepositoryPort,
        asignatura_repo: AsignaturaRepositoryPort,
        titulo_repo: TituloRepositoryPort,
        adquisicion_repo: AdquisicionRepositoryPort,
    ):
        self._extractor = file_extractor
        self._ai = ai_provider
        self._catalog = catalog
        self._carrera_repo = carrera_repo
        self._asignatura_repo = asignatura_repo
        self._titulo_repo = titulo_repo
        self._adquisicion_repo = adquisicion_repo

    # ------------------------------------------------------------------
    # Método principal
    # ------------------------------------------------------------------

    def execute(self, directory: str, facultad: str = 'Ciencias Sociales',
                carrera_default: str = 'Trabajo Social') -> None:
        """Procesa todos los archivos soportados del directorio."""
        if not os.path.exists(directory):
            print(f"Error: El directorio '{directory}' no existe.")
            return

        for filename in os.listdir(directory):
            if filename.lower().endswith(self.SUPPORTED_EXTENSIONS):
                file_path = os.path.join(directory, filename)
                print(f"Procesando {filename}")
                try:
                    self._process_single_file(file_path, facultad, carrera_default)
                except Exception as e:
                    import traceback
                    print(f"Error procesando {filename}: {e}")
                    traceback.print_exc()

    # ------------------------------------------------------------------
    # Métodos privados de dominio
    # ------------------------------------------------------------------

    def _process_single_file(self, file_path: str, facultad: str, carrera_default: str) -> None:
        """Procesa un único archivo de syllabus."""
        # 1. Extraer texto
        texto = self._extractor.extract(file_path)

        # 2. Detectar asignatura, plan y semestre
        nombre_asignatura, plan, semestre = self._extract_subject_details(texto)
        if not nombre_asignatura:
            print(f"  No se pudo extraer la asignatura de {os.path.basename(file_path)}, omitiendo.")
            return

        print(f"    Asignatura: {nombre_asignatura}")
        print(f"    Carrera (Default): {carrera_default}")
        print(f"    Plan: {plan}")
        print(f"    Semestre: {semestre}")

        # 3. Extraer bibliografía
        entries = self._extract_bibliography(texto)

        # 4. Almacenar
        self._store_bibliography(nombre_asignatura, carrera_default, entries, facultad, plan, semestre)

    @staticmethod
    def _parse_llm_json(raw: str) -> dict:
        """
        Parsea de forma robusta la respuesta JSON de un LLM.

        Estrategias en orden:
          1. Quita bloques ```json ... ``` y caracteres de control ilegales.
          2. Extrae el primer bloque { ... } completo (contando llaves).
          3. Intento directo con json.loads().
          4. json-repair: repara comillas sin escapar, truncaciones, etc.
          5. Cerrar manualmente strings/objetos abiertos.
          6. Fallback regex: extrae pares clave:valor.
        """
        import json as _json

        # --- paso 1: limpiar marcadores y ctrl chars ---
        cleaned = re.sub(r'```json\s*|```json|```', '', raw).strip()
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned)

        # --- paso 2: extraer el primer bloque { ... } contando llaves ---
        start = cleaned.find('{')
        if start != -1:
            depth = 0
            end = start
            in_string = False
            escape_next = False
            for i, ch in enumerate(cleaned[start:], start):
                if escape_next:
                    escape_next = False
                    continue
                if ch == '\\':
                    escape_next = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    continue
                if not in_string:
                    if ch == '{':
                        depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0:
                            end = i
                            break
            candidate = cleaned[start:end + 1] if depth == 0 else cleaned[start:]
        else:
            candidate = cleaned

        # --- paso 3: intento directo ---
        try:
            res = _json.loads(candidate)
            return res
        except _json.JSONDecodeError as e:
            print(f"  [DEBUG] json.loads directo falló ({e}). Intentando json-repair...")

        # --- paso 4: json-repair (maneja comillas sin escapar, truncaciones, etc.) ---
        try:
            from json_repair import repair_json
            repaired = repair_json(candidate, return_objects=True)
            if isinstance(repaired, (dict, list)):
                print("  [DEBUG] json-repair reparó el JSON exitosamente.")
                return repaired
        except Exception as e:
            print(f"  [DEBUG] json-repair falló ({e}). Intentando cierre manual...")

        # --- paso 5: cerrar strings y objetos abiertos ---
        fixed = candidate
        unescaped_quotes = len(re.findall(r'(?<!\\)"', fixed))
        if unescaped_quotes % 2 != 0:
            fixed += '"'
        open_braces = fixed.count('{') - fixed.count('}')
        open_brackets = fixed.count('[') - fixed.count(']')
        fixed += ']' * open_brackets + '}' * open_braces
        try:
            res = _json.loads(fixed)
            print("  [DEBUG] Cierre manual de llaves exitoso.")
            return res
        except _json.JSONDecodeError:
            pass

        # --- paso 6: extraer clave:valor con regex (fallback) ---
        print("  [DEBUG] Usando fallback de regex para extraer pares clave:valor...")
        result = {}
        for m in re.finditer(r'"(\w+)"\s*:\s*"([^"]*?)"', candidate):
            result[m.group(1)] = m.group(2)
        if result:
            return result

        raise ValueError(f"No se pudo parsear JSON de la respuesta LLM: {raw[:200]!r}")

    def _extract_subject_details(self, texto: str):
        """Detecta asignatura, plan y semestre del encabezado del documento."""
        texto_inicio = texto[:3000]
        prompt = f"""
Extrae la siguiente información del encabezado o primera página del syllabus:
1. Asignatura (Nombre de la materia)
2. Plan (Año del plan de estudios, ej: "2019", "2024")
3. Semestre (Número de semestre, ej: "4°", "I", "Segundo")

Texto:
{texto_inicio}

Retorna SOLO el siguiente JSON sin texto adicional:
{{"subject": "...", "plan": "...", "semester": "..."}}
"""
        try:
            resultado, _ = self._ai.generate_with_fallback(prompt, max_tokens=50000, temperature=0.1)
            datos = self._parse_llm_json(resultado)
            return datos.get('subject'), datos.get('plan'), datos.get('semester')
        except Exception as e:
            print(f"Error extrayendo detalles de asignatura: {e}")
            return None, None, None

    def _extract_bibliography_section(self, texto: str) -> str:
        """Extrae la sección de bibliografía del texto usando regex."""
        texto_lower = texto.lower()
        patron_inicio = r'(?:^|\n)(?:#+\s*|\*\*|)(bibliograf[ií]a|referencias)(?:.*)(?:$|\n)'
        match_inicio = re.search(patron_inicio, texto_lower, re.IGNORECASE)
        if match_inicio:
            return texto[match_inicio.start():]
        idx = texto_lower.find("bibliograf")
        if idx != -1:
            return texto[idx:]
        largo = len(texto)
        return texto[int(largo * 0.8):]

    def _extract_bibliography(self, texto: str) -> List[BibliographyEntry]:
        """Extrae todas las referencias bibliográficas usando IA (Gemini)."""
        bibliografia_texto = self._extract_bibliography_section(texto)
        print(f"  -> Texto de bibliografía extraído: {len(bibliografia_texto)} caracteres")

        prompt = f"""Eres un experto en bibliometría y extracción de datos estructurados.
Tu misión es extraer ABSOLUTAMENTE TODAS las referencias bibliográficas presentes en el texto del syllabus universitario adjunto.

INSTRUCCIONES CRÍTICAS DE EXHAUSTIVIDAD:
1. EXTRAE LA TOTALIDAD: En el texto suele haber entre 20 y 40 referencias bibliográficas. DEBES EXTRAERLAS TODAS, una por una, desde la primera hasta la última sin excepción. ESTÁ ESTRICTAMENTE PROHIBIDO OMITIR, RESUMIR, ACORTAR O TRUNCAR LA LISTA.
2. Clasificación:
   - Si la referencia está bajo "Bibliografía básica", "Obligatoria" o similar -> colócala en el array "basic".
   - Si está bajo "Bibliografía complementaria", "Sugerida", "Recomendada" o similar -> colócala en el array "complementary".
   - Si no hay división clara, coloca todas en "basic".
3. Tipo (type):
   - Si tiene URL, enlace web o dice "Disponible en http..." -> type="article".
   - Si es libro, manual o no tiene enlace -> type="book".
4. Capítulos: Si es un capítulo o artículo dentro de una obra o compilación (ej. "En Viveros, L. (coord.)..."), pon el título de la compilación/libro en 'title' y el del capítulo/artículo en 'chapter_title'.
5. FORMATO JSON ESTRICTO:
   - Responde ÚNICAMENTE con un objeto JSON válido.
   - Escapa adecuadamente las comillas dobles dentro de los textos o reemplázalas por comillas simples (' ').
   - NO incluyas saltos de línea literales dentro de las cadenas de texto JSON.

ESTRUCTURA DE RESPUESTA REQUERIDA (Debes llenar los arreglos con TODAS las referencias encontradas en el texto):
{{
  "basic": [
    {{"author": "Apellido, Iniciales", "normalized_author": "Nombre Apellido", "year": "2020", "title": "Título original", "normalized_title": "Título En Title Case", "publisher": "Editorial o ciudad", "url": "", "type": "book", "chapter_title": "", "language": "Español"}}
  ],
  "complementary": [
    {{"author": "Apellido, Iniciales", "normalized_author": "Nombre Apellido", "year": "2021", "title": "Título original", "normalized_title": "Título En Title Case", "publisher": "Editorial", "url": "http://...", "type": "article", "chapter_title": "", "language": "Español"}}
  ]
}}

TEXTO DE BIBLIOGRAFÍA A PROCESAR:
{bibliografia_texto}
"""
        try:
            print("  -> Usando Gemini para detección de títulos (Contexto completo)...")
            resultado = self._ai.generate_with_provider('gemini', prompt, max_tokens=50000, temperature=0.1)

            # Debug: mostrar longitud y los primeros 300 chars de la respuesta
            print(f"  -> Longitud respuesta Gemini: {len(resultado)} caracteres")
            print(f"  -> Respuesta Gemini (primeros 300 chars): {resultado[:300]!r}")

            datos = self._parse_llm_json(resultado)
            print(f"  -> Tipo de datos parseados: {type(datos).__name__}")

            # --- Normalizar la estructura de datos ---
            entries_by_type = self._normalize_bibliography_structure(datos)

            entries: List[BibliographyEntry] = []
            for bib_type, lista in entries_by_type.items():
                for item in lista:
                    if not isinstance(item, dict):
                        continue
                    entries.append(BibliographyEntry(
                        author=item.get('author', ''),
                        title=item.get('title', ''),
                        year=item.get('year'),
                        publisher=item.get('publisher'),
                        url=item.get('url'),
                        chapter_title=item.get('chapter_title'),
                        type=item.get('type', 'book'),
                        bib_type=bib_type,
                        normalized_author=item.get('normalized_author', item.get('author', '')),
                        normalized_title=item.get('normalized_title', item.get('title', '')),
                        language=item.get('language', 'Español'),
                    ))

            num_basic = sum(1 for e in entries if e.bib_type == 'basic')
            num_complementary = sum(1 for e in entries if e.bib_type == 'complementary')
            print(f"  -> Títulos detectados: {num_basic} básicos, {num_complementary} complementarios")
            return entries
        except Exception as e:
            print(f"Error extrayendo bibliografía con Gemini: {e}")
            return []

    @staticmethod
    def _normalize_bibliography_structure(datos) -> dict:
        """
        Normaliza la estructura JSON devuelta por el LLM al formato esperado:
          {"basic": [{"author":..., "title":..., ...}, ...], "complementary": [...]}

        Maneja los casos:
          - dict con listas (formato correcto)
          - lista directa de entradas
          - dict plano de una sola entrada
          - dict con valores que son strings en lugar de listas
        """
        KNOWN_TYPES = ('basic', 'complementary', 'basica', 'básica', 'complementaria')
        ENTRY_FIELDS = {'author', 'title', 'year', 'publisher', 'url', 'type', 'chapter_title'}

        if isinstance(datos, list):
            # Gemini devolvió directamente una lista de entradas
            return {'basic': datos}

        if isinstance(datos, dict):
            # Verificar si tiene listas como valores (estructura correcta)
            has_list_values = any(isinstance(v, list) for v in datos.values())
            if has_list_values:
                result = {}
                for key, val in datos.items():
                    if isinstance(val, list):
                        # Normalizar nombre de clave
                        norm_key = 'complementary' if 'complementar' in key.lower() else 'basic'
                        result.setdefault(norm_key, []).extend(val)
                    # ignorar valores que no son listas (p.ej. metadatos)
                return result if result else {'basic': []}

            # Verificar si el dict tiene las claves de una entrada bibliográfica
            # (p.ej. {"author": "...", "title": "..."} — un solo libro)
            if ENTRY_FIELDS & set(datos.keys()):
                return {'basic': [datos]}

            # Dict con valores string: posiblemente {"basic": "texto", "complementary": "texto"}
            # Convertir strings en lista vacía (dato inútil, mejor vacío que crash)
            result = {}
            for key, val in datos.items():
                norm_key = 'complementary' if 'complementar' in key.lower() else 'basic'
                if isinstance(val, list):
                    result.setdefault(norm_key, []).extend(val)
                elif isinstance(val, dict):
                    result.setdefault(norm_key, []).append(val)
                # strings se ignoran

            return result if result else {'basic': []}

        return {'basic': []}


    def _normalize_entry(self, author: str, title: str) -> dict:
        """
        Normalización heurística local instantánea (sin consumo de API ni rate limits).
        Expande espacios, aplica Title Case al título y detecta el idioma en milisegundos.
        """
        if not author:
            author = "Autor Desconocido"
        if not title:
            title = "Título Desconocido"

        # 1. Limpiar espacios extra en el autor
        norm_author = " ".join(author.strip().split())

        # 2. Aplicar Title Case al título
        norm_title = " ".join(word.capitalize() if len(word) > 3 or i == 0 else word.lower()
                              for i, word in enumerate(title.strip().split()))

        # 3. Detección rápida de idioma por palabras clave
        title_lower = title.lower()
        ing_words = {'the', 'and', 'for', 'social', 'work', 'with', 'from', 'research', 'analysis', 'study', 'education', 'practice'}
        words_in_title = set(re.findall(r'\b\w+\b', title_lower))
        language = "Inglés" if len(words_in_title.intersection(ing_words)) >= 2 else "Español"

        return {
            "normalized_author": norm_author,
            "normalized_title": norm_title,
            "language": language,
        }

    def _check_catalog_availability(self, title: Title, is_article: bool):
        """Verifica disponibilidad en catálogo Primo."""
        if is_article:
            print("  -> Artículo web detectado, no se busca en Primo")
            return False, True, None

        search_term = f"{title.normalized_title} {title.normalized_author}"
        time.sleep(3)

        try:
            detalles = self._catalog.search(search_term)
            if detalles and detalles.get('titulo') and detalles.get('autor'):
                print(f"  -> ✓ Encontrado en Primo")
                print(f"     Título de Primo: {detalles['titulo'][:80]}...")

                print("  -> Normalizando datos de Primo...")
                norm = self._normalize_entry(detalles['autor'], detalles['titulo'])

                detalles_norm = {
                    'autor_normalizado': norm['normalized_author'],
                    'titulo_normalizado': norm['normalized_title'],
                    'autor_original': detalles['autor'],
                    'titulo_original': detalles['titulo'],
                    'editor': detalles.get('editor'),
                    'fecha_creacion': detalles.get('fecha_creacion'),
                    'edicion': detalles.get('edicion'),
                    'formato': detalles.get('formato'),
                    'disponibilidad_fisica': detalles.get('disponibilidad_fisica'),
                    'disponibilidad_online': detalles.get('disponibilidad_online'),
                }

                formato = (detalles.get('formato') or '').lower()
                disponible_digital = any(k in formato for k in ('online', 'digital', 'electronic'))
                return True, disponible_digital, detalles_norm
            else:
                print("  -> ✗ No encontrado en Primo o datos incompletos")
                return False, False, None
        except Exception as e:
            print(f"  -> ✗ Error al buscar en Primo: {str(e)[:100]}")
            return False, False, None

    def _store_bibliography(self, nombre_asignatura: str, nombre_carrera: str,
                            entries: List[BibliographyEntry], facultad: str,
                            plan: str, semestre: str) -> None:
        """Persiste la bibliografía usando los repositorios."""
        # Obtener / crear carrera
        carrera = self._carrera_repo.get_or_create(nombre_carrera, facultad)

        # Obtener / crear asignatura
        asignatura = self._asignatura_repo.get_by_name_and_career(nombre_asignatura, carrera.id)
        if not asignatura:
            asignatura = self._asignatura_repo.get_or_create(nombre_asignatura, carrera)
        else:
            if plan or semestre:
                self._asignatura_repo.update_plan_and_semester(asignatura, plan, semestre)

        # Procesar cada entrada
        for entry in entries:
            print(f"Normalizando: {entry.author} - {entry.title}")
            if hasattr(entry, 'normalized_author') and entry.normalized_author and entry.normalized_title:
                norm = {
                    "normalized_author": entry.normalized_author,
                    "normalized_title": entry.normalized_title,
                    "language": getattr(entry, 'language', 'Español') or 'Español'
                }
            else:
                norm = self._normalize_entry(entry.author, entry.title)

            titulo_existente = self._titulo_repo.find_duplicate(
                norm['normalized_author'], norm['normalized_title']
            )

            if titulo_existente:
                print(f"    [DUPLICADO] ID: {titulo_existente.id}")
                self._titulo_repo.link_to_subject(titulo_existente, asignatura)
            else:
                print("    [NUEVO] Creando entrada...")
                url_articulo = entry.url
                nuevo_titulo = Title(
                    normalized_author=norm['normalized_author'],
                    normalized_title=norm['normalized_title'],
                    original_author=entry.author,
                    original_title=entry.title,
                    year=entry.year,
                    publisher=entry.publisher if not entry.is_article else url_articulo,
                    type_bib=entry.bib_type,
                    chapter=entry.chapter_title,
                    language=norm.get('language', 'Español'),
                )
                nuevo_titulo = self._titulo_repo.save(nuevo_titulo)

                impreso, digital, detalles_primo = self._check_catalog_availability(
                    nuevo_titulo, entry.is_article
                )
                encontrado_en_primo = detalles_primo is not None

                if detalles_primo:
                    nuevo_titulo.normalized_author = detalles_primo['autor_normalizado']
                    nuevo_titulo.normalized_title = detalles_primo['titulo_normalizado']
                    nuevo_titulo.original_author = detalles_primo['autor_original']
                    nuevo_titulo.original_title = detalles_primo['titulo_original']
                    if detalles_primo.get('editor'):
                        nuevo_titulo.publisher = detalles_primo['editor']
                    if detalles_primo.get('fecha_creacion'):
                        nuevo_titulo.year = detalles_primo['fecha_creacion']
                    if detalles_primo.get('edicion'):
                        nuevo_titulo.edition = detalles_primo['edicion']
                    if detalles_primo.get('formato'):
                        nuevo_titulo.format = detalles_primo['formato']
                    if detalles_primo.get('lugar'):
                        nuevo_titulo.place = detalles_primo['lugar']
                    if detalles_primo.get('disponibilidad_fisica'):
                        nuevo_titulo.physical_availability = detalles_primo['disponibilidad_fisica']
                    nuevo_titulo.online_availability = (
                        detalles_primo.get('disponibilidad_online')
                        or ("Disponible en catálogo Primo" if encontrado_en_primo else None)
                    )
                    self._titulo_repo.update(nuevo_titulo)

                adquisicion = Acquisition(
                    title_id=nuevo_titulo.id,
                    status='disponible' if (impreso or digital or encontrado_en_primo) else 'no disponible',
                    available_printed=impreso,
                    available_digital=digital or encontrado_en_primo,
                )
                self._adquisicion_repo.save(adquisicion)
                self._titulo_repo.link_to_subject(nuevo_titulo, asignatura)
