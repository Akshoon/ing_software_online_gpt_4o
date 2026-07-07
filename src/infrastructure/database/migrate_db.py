"""
Script de migración de base de datos (mantiene implementación original).
Movido a infrastructure/database/.
"""
from sqlalchemy import text
from src.infrastructure.database.db import engine


def migrate_db():
    """Agrega columnas nuevas a las tablas existentes si no existen."""
    with engine.connect() as conn:
        _add_column(conn, "ALTER TABLE titles ADD COLUMN edition TEXT", 'edition')
        _add_column(conn, "ALTER TABLE titles ADD COLUMN format TEXT", 'format')
        _add_column(conn, "ALTER TABLE titles ADD COLUMN physical_availability TEXT", 'physical_availability')
        _add_column(conn, "ALTER TABLE titles ADD COLUMN online_availability TEXT", 'online_availability')
        _add_column(conn, "ALTER TABLE subjects ADD COLUMN plan TEXT", 'plan')
        _add_column(conn, "ALTER TABLE subjects ADD COLUMN semester TEXT", 'semester')
        _add_column(conn, "ALTER TABLE titles ADD COLUMN language TEXT", 'language')
        _add_column(conn, "ALTER TABLE titles ADD COLUMN place TEXT", 'place')
        _add_column(conn, "ALTER TABLE titles ADD COLUMN chapter TEXT", 'chapter')
        conn.commit()

    print("\n[OK] Migración completada. La base de datos está lista para usar.")


def _add_column(conn, sql: str, column_name: str):
    try:
        conn.execute(text(sql))
        print(f"[OK] Columna '{column_name}' agregada exitosamente")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print(f"[OK] Columna '{column_name}' ya existe")
        else:
            print(f"Error al agregar columna '{column_name}': {e}")


if __name__ == '__main__':
    migrate_db()
