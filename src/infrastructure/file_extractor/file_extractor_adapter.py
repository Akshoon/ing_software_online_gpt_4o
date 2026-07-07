"""
Adaptador de infraestructura: FileExtractorAdapter
Implementa FileExtractorPort usando las estrategias de extracción existentes.
"""
import os

from src.domain.ports.file_extractor_port import FileExtractorPort
from src.services.file_extractor_strategies import FileProcessor


class FileExtractorAdapter(FileExtractorPort):
    """
    Adaptador que envuelve FileProcessor (Strategy Pattern) e implementa
    el puerto de dominio FileExtractorPort.
    """

    SUPPORTED_EXTENSIONS = ('.pdf', '.docx')

    def extract(self, file_path: str) -> str:
        """Extrae texto del archivo usando la estrategia apropiada."""
        processor = FileProcessor.create_for_file(file_path)
        return processor.extract_text(file_path)

    def supports(self, file_path: str) -> bool:
        """Retorna True si el tipo de archivo está soportado."""
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.SUPPORTED_EXTENSIONS
