"""
Puerto de salida: ReportPort
Define la interfaz para generar reportes de bibliografía.
"""
from abc import ABC, abstractmethod
from typing import List, Dict


class ReportPort(ABC):
    """Puerto de salida para generación y persistencia de reportes."""

    @abstractmethod
    def generate(self, data: List[Dict]) -> str:
        """
        Genera un reporte a partir de los datos.

        Args:
            data: Lista de filas del reporte

        Returns:
            Ruta al archivo generado
        """
        ...
