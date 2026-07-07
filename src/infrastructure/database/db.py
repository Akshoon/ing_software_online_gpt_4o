"""
Motor y sesión de SQLAlchemy (mantiene la implementación original intacta).
Movido a src/infrastructure/database/.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Punto fijo en la carpeta de base de datos de infraestructura
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bibliografia.db')

engine = create_engine(f'sqlite:///{DB_PATH}')
Sesion = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Crea las tablas en la base de datos."""
    from src.infrastructure.database import orm_models  # noqa: F401 - registrar modelos
    Base.metadata.create_all(engine)
