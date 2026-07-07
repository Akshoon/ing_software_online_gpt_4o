"""
Entidades de dominio puras: Career (Carrera)
No depende de ninguna tecnología de infraestructura.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Career:
    """Representa una Carrera universitaria (entidad de dominio pura)."""
    name: str
    facultad: str = 'Ciencias Sociales'
    id: int = None
