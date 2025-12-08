"""
Módulo de Repositorios con Patrón Repository

PATRÓN DE DISEÑO IMPLEMENTADO:
================================

REPOSITORY PATTERN (Patrón Repositorio)
----------------------------------------
Propósito: Abstraer el acceso a datos, proporcionando una interfaz similar a una
colección para acceder a objetos del dominio.

Beneficios:
- Separa lógica de negocio de persistencia
- Facilita cambio de base de datos
- Mejora testabilidad (fácil usar mocks)
- Centraliza consultas complejas

PRINCIPIOS SOLID APLICADOS:
============================

S - Single Responsibility Principle
    ✓ Cada repositorio maneja un solo tipo de entidad

D - Dependency Inversion Principle
    ✓ Lógica de negocio depende de repositorios (abstracción)
    ✓ No depende directamente de SQLAlchemy

Autor: Sistema de Procesamiento de Bibliografía
Versión: 2.0
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from models import Titulo, Carrera, Asignatura, Adquisicion, Sesion


class BaseRepository:
    """
    Repositorio base con operaciones CRUD comunes.
    
    PATRÓN: Repository (Base)
    PRINCIPIO: DRY (Don't Repeat Yourself)
    
    Proporciona métodos comunes para todos los repositorios.
    """
    
    def __init__(self, session: Session, model_class):
        """
        Args:
            session: Sesión de SQLAlchemy
            model_class: Clase del modelo (Titulo, Carrera, etc.)
        """
        self.session = session
        self.model_class = model_class
    
    def get_by_id(self, id: int):
        """Obtiene entidad por ID."""
        return self.session.query(self.model_class).filter_by(id=id).first()
    
    def get_all(self) -> List:
        """Obtiene todas las entidades."""
        return self.session.query(self.model_class).all()
    
    def add(self, entity):
        """Agrega una entidad."""
        self.session.add(entity)
        self.session.commit()
        return entity
    
    def delete(self, entity):
        """Elimina una entidad."""
        self.session.delete(entity)
        self.session.commit()


class TituloRepository(BaseRepository):
    """
    Repositorio para gestionar Títulos bibliográficos.
    
    PATRÓN: Repository (Concreto)
    PRINCIPIO: Single Responsibility
    """
    
    def __init__(self, session: Session = None):
        if session is None:
            session = Sesion()
        super().__init__(session, Titulo)
    
    def find_by_author_and_title(self, author: str, title: str) -> Optional[Titulo]:
        """
        Busca título por autor y título (case-insensitive).
        
        Args:
            author: Nombre del autor normalizado
            title: Título normalizado
            
        Returns:
            Titulo si existe, None si no
        """
        titulos = self.session.query(Titulo).all()
        for titulo in titulos:
            if (titulo.normalized_author.lower().strip() == author.lower().strip() and
                titulo.normalized_title.lower().strip() == title.lower().strip()):
                return titulo
        return None
    
    def find_by_asignatura(self, asignatura_id: int) -> List[Titulo]:
        """Obtiene todos los títulos de una asignatura."""
        asignatura = self.session.query(Asignatura).filter_by(id=asignatura_id).first()
        return asignatura.titulos if asignatura else []


class CarreraRepository(BaseRepository):
    """
    Repositorio para gestionar Carreras.
    
    PATRÓN: Repository (Concreto)
    """
    
    def __init__(self, session: Session = None):
        if session is None:
            session = Sesion()
        super().__init__(session, Carrera)
    
    def find_by_name(self, name: str) -> Optional[Carrera]:
        """Busca carrera por nombre."""
        return self.session.query(Carrera).filter_by(name=name).first()
    
    def get_or_create(self, name: str, facultad: str = 'Ciencias Sociales') -> Carrera:
        """Obtiene carrera existente o crea una nueva."""
        carrera = self.find_by_name(name)
        if not carrera:
            carrera = Carrera(name=name, facultad=facultad)
            self.add(carrera)
        return carrera


class AsignaturaRepository(BaseRepository):
    """
    Repositorio para gestionar Asignaturas.
    
    PATRÓN: Repository (Concreto)
    """
    
    def __init__(self, session: Session = None):
        if session is None:
            session = Sesion()
        super().__init__(session, Asignatura)
    
    def find_by_name_and_career(self, name: str, career_id: int) -> Optional[Asignatura]:
        """Busca asignatura por nombre y carrera."""
        return self.session.query(Asignatura).filter_by(
            name=name, career_id=career_id
        ).first()
    
    def get_or_create(self, name: str, carrera: Carrera) -> Asignatura:
        """Obtiene asignatura existente o crea una nueva."""
        asignatura = self.find_by_name_and_career(name, carrera.id)
        if not asignatura:
            asignatura = Asignatura(name=name, carrera=carrera)
            self.add(asignatura)
        return asignatura
