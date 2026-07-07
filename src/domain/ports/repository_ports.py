"""
Puertos de repositorios (secondary ports).
El dominio define estas interfaces; la infraestructura las implementa.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.career import Career
from src.domain.entities.subject import Subject
from src.domain.entities.title import Title
from src.domain.entities.acquisition import Acquisition


class CarreraRepositoryPort(ABC):
    """Puerto de salida para persistencia de Carreras."""

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Career]:
        ...

    @abstractmethod
    def get_or_create(self, name: str, facultad: str = 'Ciencias Sociales') -> Career:
        ...

    @abstractmethod
    def get_all(self) -> List[Career]:
        ...


class AsignaturaRepositoryPort(ABC):
    """Puerto de salida para persistencia de Asignaturas."""

    @abstractmethod
    def get_by_name_and_career(self, name: str, career_id: int) -> Optional[Subject]:
        ...

    @abstractmethod
    def get_or_create(self, name: str, career: Career) -> Subject:
        ...

    @abstractmethod
    def update_plan_and_semester(self, subject: Subject, plan: str, semester: str) -> None:
        ...


class TituloRepositoryPort(ABC):
    """Puerto de salida para persistencia de Títulos bibliográficos."""

    @abstractmethod
    def find_duplicate(self, normalized_author: str, normalized_title: str) -> Optional[Title]:
        ...

    @abstractmethod
    def save(self, title: Title) -> Title:
        ...

    @abstractmethod
    def update(self, title: Title) -> None:
        ...

    @abstractmethod
    def link_to_subject(self, title: Title, subject: Subject) -> None:
        ...

    @abstractmethod
    def get_all_with_relations(self) -> List:
        """Devuelve todos los títulos con sus relaciones (para reportes)."""
        ...


class AdquisicionRepositoryPort(ABC):
    """Puerto de salida para persistencia de Adquisiciones."""

    @abstractmethod
    def get_by_title(self, title_id: int) -> Optional[Acquisition]:
        ...

    @abstractmethod
    def save(self, acquisition: Acquisition) -> Acquisition:
        ...

    @abstractmethod
    def get_all_available(self) -> List[Acquisition]:
        ...
