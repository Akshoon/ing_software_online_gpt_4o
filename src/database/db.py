"""
Shim de compatibilidad: re-exporta desde src/infrastructure/database/.
"""
from src.infrastructure.database.db import Sesion, Base, engine, init_db

__all__ = ['Sesion', 'Base', 'engine', 'init_db']
