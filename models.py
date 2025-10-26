from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Boolean, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

# Tabla de relación muchos a muchos entre títulos y asignaturas
titulo_asignatura = Table('title_subject', Base.metadata,
    Column('title_id', Integer, ForeignKey('titles.id')),
    Column('subject_id', Integer, ForeignKey('subjects.id'))
)

class Carrera(Base):
    __tablename__ = 'careers'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    facultad = Column(String, nullable=False, default='Ciencias Sociales')
    asignaturas = relationship('Asignatura', back_populates='carrera')

class Asignatura(Base):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    career_id = Column(Integer, ForeignKey('careers.id'))
    carrera = relationship('Carrera', back_populates='asignaturas')
    titulos = relationship('Titulo', secondary=titulo_asignatura, back_populates='asignaturas')

class Titulo(Base):
    __tablename__ = 'titles'
    id = Column(Integer, primary_key=True)
    normalized_author = Column(String)
    normalized_title = Column(String)
    original_author = Column(String)
    original_title = Column(String)
    year = Column(String)
    publisher = Column(String)
    edition = Column(String)  # Edición del libro (de Primo)
    format = Column(String)   # Formato del libro (de Primo)
    physical_availability = Column(String)  # Disponibilidad física (ej: "16 copias, 16 disponible")
    online_availability = Column(String)  # Disponibilidad online (ej: "Texto completo disponible")
    type_bib = Column(String)  # basica o complementaria
    asignaturas = relationship('Asignatura', secondary=titulo_asignatura, back_populates='titulos')
    adquisiciones = relationship('Adquisicion', back_populates='titulo')

class Adquisicion(Base):
    __tablename__ = 'acquisitions'
    id = Column(Integer, primary_key=True)
    title_id = Column(Integer, ForeignKey('titles.id'))
    titulo = relationship('Titulo', back_populates='adquisiciones')
    status = Column(String)  # cotizado, comprado, procesado, activado
    available_printed = Column(Boolean, default=False)
    available_digital = Column(Boolean, default=False)

motor = create_engine('sqlite:///bibliografia.db')
Base.metadata.create_all(motor)
Sesion = sessionmaker(bind=motor)
