"""
Shim de compatibilidad: re-exporta desde infrastructure.
"""
from src.infrastructure.database.sqlalchemy_repositories import (
    SQLAlchemyCarreraRepository as CarreraRepository,
    SQLAlchemyAsignaturaRepository as AsignaturaRepository,
    SQLAlchemyTituloRepository as TituloRepository,
    SQLAlchemyAdquisicionRepository as AdquisicionRepository,
)

# También re-exportar las originales para compatibilidad con tests
BaseRepository = object  # Placeholder

__all__ = [
    'CarreraRepository', 'AsignaturaRepository', 'TituloRepository',
    'AdquisicionRepository', 'BaseRepository',
]
