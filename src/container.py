"""
Contenedor de dependencias (Composition Root).
Aquí se ensamblan todos los adaptadores con los casos de uso.
Es el único lugar donde se conocen todas las implementaciones concretas.
"""
from src.infrastructure.database.db import Sesion
from src.infrastructure.database.sqlalchemy_repositories import (
    SQLAlchemyCarreraRepository,
    SQLAlchemyAsignaturaRepository,
    SQLAlchemyTituloRepository,
    SQLAlchemyAdquisicionRepository,
)
from src.infrastructure.ai.ai_provider_adapter import AIProviderAdapter
from src.infrastructure.catalog.primo_catalog_adapter import PrimoCatalogAdapter
from src.infrastructure.file_extractor.file_extractor_adapter import FileExtractorAdapter
from src.infrastructure.report.csv_report_adapter import CsvReportAdapter

from src.domain.use_cases.process_files_use_case import ProcessFilesUseCase
from src.domain.use_cases.generate_report_use_case import GenerateReportUseCase
from src.domain.use_cases.notify_careers_use_case import NotifyCareersUseCase
from src.domain.use_cases.import_csv_use_case import ImportCsvUseCase


def _create_shared_session():
    """Crea una sesión de base de datos compartida para todos los repositorios."""
    return Sesion()


def build_process_files_use_case() -> ProcessFilesUseCase:
    """Construye y retorna el caso de uso ProcessFilesUseCase con sus dependencias."""
    session = _create_shared_session()
    ai_provider = AIProviderAdapter()
    return ProcessFilesUseCase(
        file_extractor=FileExtractorAdapter(),
        ai_provider=ai_provider,
        catalog=PrimoCatalogAdapter(),
        carrera_repo=SQLAlchemyCarreraRepository(session),
        asignatura_repo=SQLAlchemyAsignaturaRepository(session),
        titulo_repo=SQLAlchemyTituloRepository(session),
        adquisicion_repo=SQLAlchemyAdquisicionRepository(session),
    )


def build_generate_report_use_case() -> GenerateReportUseCase:
    """Construye y retorna el caso de uso GenerateReportUseCase con sus dependencias."""
    session = _create_shared_session()
    return GenerateReportUseCase(
        carrera_repo=SQLAlchemyCarreraRepository(session),
        adquisicion_repo=SQLAlchemyAdquisicionRepository(session),
        report_port=CsvReportAdapter(),
    )


def build_notify_careers_use_case() -> NotifyCareersUseCase:
    """Construye y retorna el caso de uso NotifyCareersUseCase con sus dependencias."""
    session = _create_shared_session()
    return NotifyCareersUseCase(
        adquisicion_repo=SQLAlchemyAdquisicionRepository(session),
    )


def build_import_csv_use_case() -> ImportCsvUseCase:
    """Construye y retorna el caso de uso ImportCsvUseCase."""
    return ImportCsvUseCase()
