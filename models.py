"""
Módulo de Modelos de Datos con Patrón Active Record

PATRÓN DE DISEÑO IMPLEMENTADO:
================================

ACTIVE RECORD PATTERN (Patrón Registro Activo)
-----------------------------------------------
Propósito: Un objeto que encapsula una fila de una tabla de base de datos,
encapsula el acceso a la base de datos y agrega lógica de dominio sobre esos datos.

Implementado mediante: SQLAlchemy ORM

Beneficios:
- Mapeo objeto-relacional transparente
- Simplifica acceso a datos
- Validaciones y lógica de negocio en el modelo
- Relaciones entre entidades bien definidas

PRINCIPIOS SOLID APLICADOS:
============================

S - Single Responsibility Principle
    ✓ Cada modelo representa una entidad del dominio
    ✓ Responsabilidad: Representar y persistir datos de esa entidad

ARQUITECTURA DE BASE DE DATOS:
===============================

Relaciones:
- Carrera 1:N Asignatura (Una carrera tiene muchas asignaturas)
- Asignatura N:M Titulo (Relación muchos a muchos)
- Titulo 1:N Adquisicion (Un título puede tener múltiples adquisiciones)

Autor: Sistema de Procesamiento de Bibliografía
Versión: 2.0
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Boolean, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Base declarativa para todos los modelos
# PATRÓN: Active Record - Base para mapeo objeto-relacional
Base = declarative_base()


# ============================================================================
# TABLA DE ASOCIACIÓN: Relación Muchos a Muchos
# ============================================================================

# Tabla de relación muchos a muchos entre títulos y asignaturas
# PATRÓN: Association Table - Implementa relación N:M
titulo_asignatura = Table('title_subject', Base.metadata,
    Column('title_id', Integer, ForeignKey('titles.id')),
    Column('subject_id', Integer, ForeignKey('subjects.id'))
)


# ============================================================================
# MODELOS DE DOMINIO
# ============================================================================

class Carrera(Base):
    """
    Modelo que representa una Carrera universitaria.
    
    PATRÓN: Active Record
    PRINCIPIO: Single Responsibility - Representa y persiste datos de Carrera
    
    Relaciones:
        - 1:N con Asignatura (Una carrera tiene muchas asignaturas)
    
    Atributos:
        id (int): Identificador único
        name (str): Nombre de la carrera (único)
        facultad (str): Facultad a la que pertenece
        asignaturas (List[Asignatura]): Lista de asignaturas de la carrera
    
    Ejemplo:
        >>> carrera = Carrera(name="Trabajo Social", facultad="Ciencias Sociales")
        >>> session.add(carrera)
        >>> session.commit()
    """
    __tablename__ = 'careers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    facultad = Column(String, nullable=False, default='Ciencias Sociales')
    
    # Relación 1:N con Asignatura
    asignaturas = relationship('Asignatura', back_populates='carrera')


class Asignatura(Base):
    """
    Modelo que representa una Asignatura.
    
    PATRÓN: Active Record
    PRINCIPIO: Single Responsibility - Representa y persiste datos de Asignatura
    
    Relaciones:
        - N:1 con Carrera (Muchas asignaturas pertenecen a una carrera)
        - N:M con Titulo (Una asignatura puede tener muchos títulos y viceversa)
    
    Atributos:
        id (int): Identificador único
        name (str): Nombre de la asignatura
        career_id (int): ID de la carrera a la que pertenece
        carrera (Carrera): Carrera a la que pertenece
        titulos (List[Titulo]): Lista de títulos bibliográficos
    
    Ejemplo:
        >>> asignatura = Asignatura(name="Sociología I", carrera=carrera)
        >>> session.add(asignatura)
    """
    __tablename__ = 'subjects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    career_id = Column(Integer, ForeignKey('careers.id'))
    plan = Column(String)      # Plan (año)
    semester = Column(String)  # Semestre
    
    # Relaciones
    carrera = relationship('Carrera', back_populates='asignaturas')
    titulos = relationship('Titulo', secondary=titulo_asignatura, back_populates='asignaturas')


class Titulo(Base):
    """
    Modelo que representa un Título bibliográfico.
    
    PATRÓN: Active Record
    PRINCIPIO: Single Responsibility - Representa y persiste datos de Título
    
    Relaciones:
        - N:M con Asignatura (Un título puede estar en muchas asignaturas)
        - 1:N con Adquisicion (Un título puede tener múltiples adquisiciones)
    
    Atributos:
        id (int): Identificador único
        normalized_author (str): Autor normalizado
        normalized_title (str): Título normalizado
        original_author (str): Autor original del documento
        original_title (str): Título original del documento
        year (str): Año de publicación
        publisher (str): Editorial o URL (si es artículo web)
        edition (str): Edición del libro
        format (str): Formato (impreso, digital, etc.)
        physical_availability (str): Disponibilidad física
        online_availability (str): Disponibilidad online
        type_bib (str): Tipo de bibliografía (básica/complementaria)
        asignaturas (List[Asignatura]): Asignaturas que usan este título
        adquisiciones (List[Adquisicion]): Historial de adquisiciones
    
    Ejemplo:
        >>> titulo = Titulo(
        ...     normalized_author="Danilo Martuccelli",
        ...     normalized_title="Cambio de Rumbo",
        ...     year="2007"
        ... )
    """
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
    physical_availability = Column(String)  # Disponibilidad física
    online_availability = Column(String)  # Disponibilidad online
    language = Column(String)  # Idioma del libro
    type_bib = Column(String)  # básica o complementaria
    
    # Relaciones
    asignaturas = relationship('Asignatura', secondary=titulo_asignatura, back_populates='titulos')
    adquisiciones = relationship('Adquisicion', back_populates='titulo')


class Adquisicion(Base):
    """
    Modelo que representa una Adquisición de título.
    
    PATRÓN: Active Record
    PRINCIPIO: Single Responsibility - Representa y persiste datos de Adquisición
    
    Relaciones:
        - N:1 con Titulo (Muchas adquisiciones pueden ser del mismo título)
    
    Atributos:
        id (int): Identificador único
        title_id (int): ID del título adquirido
        titulo (Titulo): Título adquirido
        status (str): Estado (cotizado, comprado, procesado, activado)
        available_printed (bool): Disponible en formato impreso
        available_digital (bool): Disponible en formato digital
    
    Ejemplo:
        >>> adquisicion = Adquisicion(
        ...     titulo=titulo,
        ...     status='disponible',
        ...     available_printed=True,
        ...     available_digital=True
        ... )
    """
    __tablename__ = 'acquisitions'
    
    id = Column(Integer, primary_key=True)
    title_id = Column(Integer, ForeignKey('titles.id'))
    
    # Relación con Titulo
    titulo = relationship('Titulo', back_populates='adquisiciones')
    
    status = Column(String)  # cotizado, comprado, procesado, activado
    available_printed = Column(Boolean, default=False)
    available_digital = Column(Boolean, default=False)


# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================

# Motor de base de datos SQLite
# PATRÓN: Singleton implícito - Una sola conexión a la BD
motor = create_engine('sqlite:///bibliografia.db')

# Crear todas las tablas
Base.metadata.create_all(motor)

# Factory de sesiones
# PATRÓN: Factory - Crea sesiones de base de datos
Sesion = sessionmaker(bind=motor)
