"""
Shim de compatibilidad: re-exporta desde src/infrastructure/database/.
La implementación real está en src/infrastructure/database/.
"""
from src.infrastructure.database.orm_models import (
    CarreraORM as Carrera,
    AsignaturaORM as Asignatura,
    TituloORM as Titulo,
    AdquisicionORM as Adquisicion,
    titulo_asignatura,
)
from src.infrastructure.database.db import Sesion, Base, engine, init_db
from src.infrastructure.database.migrate_db import migrate_db

__all__ = [
    'Carrera', 'Asignatura', 'Titulo', 'Adquisicion', 'titulo_asignatura',
    'Sesion', 'Base', 'engine', 'init_db', 'migrate_db',
]
