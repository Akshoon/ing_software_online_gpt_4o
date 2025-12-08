"""
Script para migrar la base de datos y agregar las columnas edition, format, physical_availability y online_availability
"""
from sqlalchemy import text
from src.database.db import engine

def migrate_db():
    # Conectar a la base de datos usando el engine compartido

    with engine.connect() as conn:
        try:
            # Agregar columna edition si no existe
            conn.execute(text("ALTER TABLE titles ADD COLUMN edition TEXT"))
            print("✓ Columna 'edition' agregada exitosamente")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ Columna 'edition' ya existe")
            else:
                print(f"Error al agregar columna 'edition': {e}")

        try:
            # Agregar columna format si no existe
            conn.execute(text("ALTER TABLE titles ADD COLUMN format TEXT"))
            print("✓ Columna 'format' agregada exitosamente")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ Columna 'format' ya existe")
            else:
                print(f"Error al agregar columna 'format': {e}")

        try:
            # Agregar columna physical_availability si no existe
            conn.execute(text("ALTER TABLE titles ADD COLUMN physical_availability TEXT"))
            print("✓ Columna 'physical_availability' agregada exitosamente")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ Columna 'physical_availability' ya existe")
            else:
                print(f"Error al agregar columna 'physical_availability': {e}")

        try:
            # Agregar columna online_availability si no existe
            conn.execute(text("ALTER TABLE titles ADD COLUMN online_availability TEXT"))
            print("✓ Columna 'online_availability' agregada exitosamente")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ Columna 'online_availability' ya existe")
            else:
                print(f"Error al agregar columna 'online_availability': {e}")

        try:
            # Agregar columna plan a subjects
            conn.execute(text("ALTER TABLE subjects ADD COLUMN plan TEXT"))
            print("✓ Columna 'plan' agregada exitosamente a subjects")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ Columna 'plan' ya existe en subjects")
            else:
                print(f"Error al agregar columna 'plan': {e}")

        try:
            # Agregar columna semester a subjects
            conn.execute(text("ALTER TABLE subjects ADD COLUMN semester TEXT"))
            print("✓ Columna 'semester' agregada exitosamente a subjects")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ Columna 'semester' ya existe en subjects")
            else:
                print(f"Error al agregar columna 'semester': {e}")

        try:
            # Agregar columna language a titles
            conn.execute(text("ALTER TABLE titles ADD COLUMN language TEXT"))
            print("✓ Columna 'language' agregada exitosamente a titles")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ Columna 'language' ya existe en titles")
            else:
                print(f"Error al agregar columna 'language': {e}")

        try:
            # Agregar columna place a titles
            conn.execute(text("ALTER TABLE titles ADD COLUMN place TEXT"))
            print("✓ Columna 'place' agregada exitosamente a titles")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ Columna 'place' ya existe en titles")
            else:
                print(f"Error al agregar columna 'place': {e}")

        try:
            # Agregar columna chapter a titles
            conn.execute(text("ALTER TABLE titles ADD COLUMN chapter TEXT"))
            print("✓ Columna 'chapter' agregada exitosamente a titles")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ Columna 'chapter' ya existe en titles")
            else:
                print(f"Error al agregar columna 'chapter': {e}")

        conn.commit()

    print("\n✓ Migración completada. La base de datos está lista para usar.")

if __name__ == '__main__':
    migrate_db()
