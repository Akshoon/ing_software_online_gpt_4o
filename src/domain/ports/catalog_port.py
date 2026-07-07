"""
Puerto de salida: CatalogSearchPort
Define la interfaz para buscar libros en catálogos externos (Primo, etc.).
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict


class CatalogSearchPort(ABC):
    """Puerto de salida para búsqueda en catálogos bibliotecarios externos."""

    @abstractmethod
    def search(self, search_term: str) -> Optional[Dict]:
        """
        Busca un libro en el catálogo.

        Args:
            search_term: Término de búsqueda (título + autor)

        Returns:
            Diccionario con detalles del libro o None si no se encuentra:
            {
                'titulo': str,
                'autor': str,
                'editor': str,
                'fecha_creacion': str,
                'edicion': str,
                'formato': str,
                'lugar': str,
                'disponibilidad_fisica': str,
                'disponibilidad_online': str
            }
        """
        ...
