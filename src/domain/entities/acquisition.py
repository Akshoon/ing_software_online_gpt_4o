"""
Entidades de dominio puras: Acquisition (Adquisición)
No depende de ninguna tecnología de infraestructura.
"""
from dataclasses import dataclass


@dataclass
class Acquisition:
    """Representa una Adquisición de título (entidad de dominio pura)."""
    title_id: int
    status: str = 'no disponible'
    available_printed: bool = False
    available_digital: bool = False
    id: int = None
