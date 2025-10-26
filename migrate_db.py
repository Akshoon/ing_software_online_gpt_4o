"""
Script para migrar la base de datos y agregar las columnas edition, format, physical_availability y online_availability
"""
from sqlalchemy import create_engine, text

def migrate_db():
    # Conectar a la base de datos
    engine = create_engine('sqlite:///bibliografia.db')

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

        conn.commit()

    print("\n✓ Migración completada. La base de datos está lista para usar.")

if __name__ == '__main__':
    migrate_db()
