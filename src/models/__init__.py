"""
Shim de compatibilidad: re-exporta modelos ORM desde su nueva ubicación.
La implementación real está en src/infrastructure/database/orm_models.py
"""
from src.infrastructure.database.orm_models import (
    CarreraORM as Carrera,
    AsignaturaORM as Asignatura,
    TituloORM as Titulo,
    AdquisicionORM as Adquisicion,
    titulo_asignatura,
)

__all__ = ['Carrera', 'Asignatura', 'Titulo', 'Adquisicion', 'titulo_asignatura']
