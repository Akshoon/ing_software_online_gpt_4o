"""
Shim de compatibilidad: re-exporta desde infrastructure.
"""
from src.infrastructure.database.migrate_db import migrate_db

__all__ = ['migrate_db']
