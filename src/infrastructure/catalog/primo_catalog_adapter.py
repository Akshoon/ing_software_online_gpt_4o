"""
Adaptador de infraestructura: PrimoCatalogAdapter
Implementa CatalogSearchPort usando el scraper de Primo existente.
"""
from typing import Optional, Dict

from src.domain.ports.catalog_port import CatalogSearchPort
from src.services.scraper_primo import buscar_libro_detalles


class PrimoCatalogAdapter(CatalogSearchPort):
    """
    Adaptador que envuelve buscar_libro_detalles() e implementa
    el puerto de dominio CatalogSearchPort.
    """

    def search(self, search_term: str) -> Optional[Dict]:
        """Busca un libro en el catálogo Primo de la UAH."""
        return buscar_libro_detalles(search_term, verbose=False)
