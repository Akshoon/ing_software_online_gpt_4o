"""
Modelos ORM de SQLAlchemy (mantiene la implementación original intacta).
Solo se mueve al paquete de infraestructura de base de datos.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from src.infrastructure.database.db import Base


# Tabla de relación muchos a muchos entre títulos y asignaturas
titulo_asignatura = Table('title_subject', Base.metadata,
    Column('title_id', Integer, ForeignKey('titles.id')),
    Column('subject_id', Integer, ForeignKey('subjects.id'))
)


class CarreraORM(Base):
    """Modelo ORM para Carrera."""
    __tablename__ = 'careers'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    facultad = Column(String, nullable=False, default='Ciencias Sociales')

    asignaturas = relationship('AsignaturaORM', back_populates='carrera')


class AsignaturaORM(Base):
    """Modelo ORM para Asignatura."""
    __tablename__ = 'subjects'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    career_id = Column(Integer, ForeignKey('careers.id'))
    plan = Column(String)
    semester = Column(String)

    carrera = relationship('CarreraORM', back_populates='asignaturas')
    titulos = relationship('TituloORM', secondary=titulo_asignatura, back_populates='asignaturas')


class TituloORM(Base):
    """Modelo ORM para Título bibliográfico."""
    __tablename__ = 'titles'

    id = Column(Integer, primary_key=True)
    normalized_author = Column(String)
    normalized_title = Column(String)
    original_author = Column(String)
    original_title = Column(String)
    year = Column(String)
    publisher = Column(String)
    edition = Column(String)
    format = Column(String)
    physical_availability = Column(String)
    online_availability = Column(String)
    place = Column(String)
    chapter = Column(String)
    language = Column(String)
    type_bib = Column(String)

    asignaturas = relationship('AsignaturaORM', secondary=titulo_asignatura, back_populates='titulos')
    adquisiciones = relationship('AdquisicionORM', back_populates='titulo')


class AdquisicionORM(Base):
    """Modelo ORM para Adquisición."""
    __tablename__ = 'acquisitions'

    id = Column(Integer, primary_key=True)
    title_id = Column(Integer, ForeignKey('titles.id'))

    titulo = relationship('TituloORM', back_populates='adquisiciones')

    status = Column(String)
    available_printed = Column(Boolean, default=False)
    available_digital = Column(Boolean, default=False)
