"""
Caso de uso: GenerateReportUseCase
Genera el reporte CSV consolidado con toda la información bibliográfica.
Solo depende de puertos, no de implementaciones concretas.
"""
import re
from typing import List, Dict

from src.domain.ports.repository_ports import (
    CarreraRepositoryPort,
    AdquisicionRepositoryPort,
)
from src.domain.ports.report_port import ReportPort


def _extraer_numero_copias(disponibilidad_fisica: str) -> int:
    """Extrae el número de copias del string de disponibilidad física."""
    if not disponibilidad_fisica:
        return 0
    match = re.search(r'(\d+)\s+copias?', disponibilidad_fisica, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0


class GenerateReportUseCase:
    """
    Genera un reporte consolidado en CSV con la información bibliográfica
    de todas las carreras.
    """

    def __init__(
        self,
        carrera_repo: CarreraRepositoryPort,
        adquisicion_repo: AdquisicionRepositoryPort,
        report_port: ReportPort,
    ):
        self._carrera_repo = carrera_repo
        self._adquisicion_repo = adquisicion_repo
        self._report_port = report_port

    def execute(self) -> str:
        """Genera el reporte y retorna la ruta del archivo generado."""
        datos = self._build_report_data()
        return self._report_port.generate(datos)

    def _build_report_data(self) -> List[Dict]:
        """Construye la lista de filas del reporte."""
        datos = []
        carreras = self._carrera_repo.get_all()

        for carrera in carreras:
            for asignatura in carrera.asignaturas:
                for titulo in asignatura.titulos:
                    adquisicion = self._adquisicion_repo.get_by_title(titulo.id)

                    num_copias_fisicas = _extraer_numero_copias(titulo.physical_availability)
                    disponible_online = 1 if (adquisicion and adquisicion.available_digital) else 0

                    es_articulo = (
                        titulo.publisher
                        and ('http' in titulo.publisher.lower() or 'www' in titulo.publisher.lower())
                    )

                    conteo_carrera = sum(
                        1 for asig in titulo.asignaturas if asig.career_id == carrera.id
                    )
                    conteo_global = len(titulo.asignaturas)

                    datos.append({
                        'Facultad': carrera.facultad or '',
                        'Carrera ': carrera.name or '',
                        'Asignatura ': asignatura.name or '',
                        'Plan (año)': asignatura.plan or '',
                        'Semestre': asignatura.semester or '',
                        'Autor (Apellido, Nombre) ': titulo.normalized_author or '',
                        'Título del libro/revistas (Información completa del título)': titulo.normalized_title or '',
                        'Capitulo o artículo si se amerita la información': titulo.chapter or '',
                        'Edición': titulo.edition or '',
                        'Lugar de Públicación ': titulo.place or '',
                        'Editorial / Si es articulo de revista, Volumen, No': titulo.publisher or '',
                        'Año de Publicación': titulo.year or '',
                        'Idioma': titulo.language or 'Español',
                        'Tipo Bibliografía (Básica / Complementaria) ': titulo.type_bib or '',
                        'Tipo de Formato': titulo.format or (
                            'Digital' if disponible_online
                            else ('Impreso' if num_copias_fisicas > 0 else '')
                        ),
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
                        'Títulos en Biblioteca': 1 if (
                            adquisicion and (adquisicion.available_printed or adquisicion.available_digital)
                        ) else 0,
                    })
        return datos
