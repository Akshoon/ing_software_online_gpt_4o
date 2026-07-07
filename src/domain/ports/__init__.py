"""
Puertos de salida (secondary/driven ports):
Interfaces que el dominio define y la infraestructura implementa.
"""
from .repository_ports import (
    CarreraRepositoryPort,
    AsignaturaRepositoryPort,
    TituloRepositoryPort,
    AdquisicionRepositoryPort,
)
from .ai_port import AIProviderPort
from .catalog_port import CatalogSearchPort
from .file_extractor_port import FileExtractorPort
from .report_port import ReportPort
