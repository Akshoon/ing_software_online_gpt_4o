from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Get the directory where this file serves as the base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Point to the database file in the same directory (src/database/bibliografia.db)
DB_PATH = os.path.join(BASE_DIR, 'bibliografia.db')

# Use absolute path for sqlite to avoid relative path issues
engine = create_engine(f'sqlite:///{DB_PATH}')

# Session factory
Sesion = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()

def init_db():
    """Crea las tablas en la base de datos."""
    # Importar modelos aquí para asegurar que estén registrados en Base.metadata
    from src.models import models
    Base.metadata.create_all(engine)
