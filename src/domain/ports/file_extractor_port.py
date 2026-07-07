"""
Puerto de salida: FileExtractorPort
Define la interfaz para extraer texto de archivos (PDF, Word, etc.).
"""
from abc import ABC, abstractmethod


class FileExtractorPort(ABC):
    """Puerto de salida para extracción de texto de archivos."""

    @abstractmethod
    def extract(self, file_path: str) -> str:
        """
        Extrae el contenido textual de un archivo.

        Args:
            file_path: Ruta absoluta al archivo

        Returns:
            Texto extraído (preferiblemente en formato Markdown)

        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el tipo de archivo no está soportado
        """
        ...

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """Retorna True si este extractor soporta el tipo de archivo."""
        ...
