"""
Entidades de dominio puras: Title (Título bibliográfico)
No depende de ninguna tecnología de infraestructura.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Title:
    """Representa un Título bibliográfico (entidad de dominio pura)."""
    normalized_author: str
    normalized_title: str
    original_author: str = None
    original_title: str = None
    year: Optional[str] = None
    publisher: Optional[str] = None
    edition: Optional[str] = None
    format: Optional[str] = None
    physical_availability: Optional[str] = None
    online_availability: Optional[str] = None
    place: Optional[str] = None
    chapter: Optional[str] = None
    language: Optional[str] = 'Español'
    type_bib: Optional[str] = None
    id: int = None
