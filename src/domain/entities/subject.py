"""
Entidades de dominio puras: Subject (Asignatura)
No depende de ninguna tecnología de infraestructura.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Subject:
    """Representa una Asignatura universitaria (entidad de dominio pura)."""
    name: str
    career_id: int = None
    plan: Optional[str] = None
    semester: Optional[str] = None
    id: int = None
