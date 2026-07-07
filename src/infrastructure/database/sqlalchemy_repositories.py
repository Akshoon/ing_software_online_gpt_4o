"""
Implementaciones SQLAlchemy de los puertos de repositorio.
Adaptan los modelos ORM a las entidades de dominio puras.
"""
from typing import List, Optional

from src.domain.entities.career import Career
from src.domain.entities.subject import Subject
from src.domain.entities.title import Title
from src.domain.entities.acquisition import Acquisition
from src.domain.ports.repository_ports import (
    CarreraRepositoryPort,
    AsignaturaRepositoryPort,
    TituloRepositoryPort,
    AdquisicionRepositoryPort,
)
from src.infrastructure.database.db import Sesion
from src.infrastructure.database.orm_models import (
    CarreraORM, AsignaturaORM, TituloORM, AdquisicionORM
)


# ---------------------------------------------------------------------------
# Helpers de conversión ORM <-> Domain Entity
# ---------------------------------------------------------------------------

def _orm_to_career(orm: CarreraORM) -> Career:
    c = Career(name=orm.name, facultad=orm.facultad, id=orm.id)
    # Adjuntamos la lista ORM de asignaturas para que GenerateReportUseCase pueda iterar
    c.asignaturas = [_orm_to_subject(a) for a in orm.asignaturas]
    return c


def _orm_to_subject(orm: AsignaturaORM) -> Subject:
    s = Subject(
        name=orm.name,
        career_id=orm.career_id,
        plan=orm.plan,
        semester=orm.semester,
        id=orm.id,
    )
    # Lazy: adjuntamos los títulos ORM para iteración en reporte
    s.titulos = [_orm_to_title(t) for t in orm.titulos]
    return s


def _orm_to_title(orm: TituloORM) -> Title:
    t = Title(
        normalized_author=orm.normalized_author or '',
        normalized_title=orm.normalized_title or '',
        original_author=orm.original_author,
        original_title=orm.original_title,
        year=orm.year,
        publisher=orm.publisher,
        edition=orm.edition,
        format=orm.format,
        physical_availability=orm.physical_availability,
        online_availability=orm.online_availability,
        place=orm.place,
        chapter=orm.chapter,
        language=orm.language,
        type_bib=orm.type_bib,
        id=orm.id,
    )
    # Para reportes
    t.asignaturas = [
        type('SubjectRef', (), {'career_id': a.career_id, 'name': a.name})()
        for a in orm.asignaturas
    ]
    return t


def _orm_to_acquisition(orm: AdquisicionORM) -> Acquisition:
    a = Acquisition(
        title_id=orm.title_id,
        status=orm.status,
        available_printed=orm.available_printed,
        available_digital=orm.available_digital,
        id=orm.id,
    )
    # Para NotifyCareersUseCase
    a.titulo = orm.titulo
    return a


# ---------------------------------------------------------------------------
# Repositorios concretos
# ---------------------------------------------------------------------------

class SQLAlchemyCarreraRepository(CarreraRepositoryPort):
    """Repositorio de Carrera usando SQLAlchemy."""

    def __init__(self, session=None):
        self._session = session or Sesion()

    def get_by_name(self, name: str) -> Optional[Career]:
        orm = self._session.query(CarreraORM).filter_by(name=name).first()
        return _orm_to_career(orm) if orm else None

    def get_or_create(self, name: str, facultad: str = 'Ciencias Sociales') -> Career:
        orm = self._session.query(CarreraORM).filter_by(name=name).first()
        if not orm:
            orm = CarreraORM(name=name, facultad=facultad)
            self._session.add(orm)
            self._session.commit()
        return _orm_to_career(orm)

    def get_all(self) -> List[Career]:
        orms = self._session.query(CarreraORM).all()
        return [_orm_to_career(o) for o in orms]


class SQLAlchemyAsignaturaRepository(AsignaturaRepositoryPort):
    """Repositorio de Asignatura usando SQLAlchemy."""

    def __init__(self, session=None):
        self._session = session or Sesion()

    def get_by_name_and_career(self, name: str, career_id: int) -> Optional[Subject]:
        orm = self._session.query(AsignaturaORM).filter_by(
            name=name, career_id=career_id
        ).first()
        return _orm_to_subject(orm) if orm else None

    def get_or_create(self, name: str, career: Career) -> Subject:
        # Necesitamos el ORM de la carrera para crear la asignatura ORM
        carrera_orm = self._session.query(CarreraORM).filter_by(id=career.id).first()
        orm = self._session.query(AsignaturaORM).filter_by(
            name=name, career_id=career.id
        ).first()
        if not orm:
            orm = AsignaturaORM(name=name, carrera=carrera_orm)
            self._session.add(orm)
            self._session.commit()
        return _orm_to_subject(orm)

    def update_plan_and_semester(self, subject: Subject, plan: str, semester: str) -> None:
        orm = self._session.query(AsignaturaORM).filter_by(id=subject.id).first()
        if orm:
            if plan:
                orm.plan = plan
            if semester:
                orm.semester = semester
            self._session.commit()


class SQLAlchemyTituloRepository(TituloRepositoryPort):
    """Repositorio de Título usando SQLAlchemy."""

    def __init__(self, session=None):
        self._session = session or Sesion()

    def find_duplicate(self, normalized_author: str, normalized_title: str) -> Optional[Title]:
        all_titles = self._session.query(TituloORM).all()
        for orm in all_titles:
            if (orm.normalized_author and orm.normalized_title and
                orm.normalized_author.lower().strip() == normalized_author.lower().strip() and
                    orm.normalized_title.lower().strip() == normalized_title.lower().strip()):
                return _orm_to_title(orm)
        return None

    def save(self, title: Title) -> Title:
        orm = TituloORM(
            normalized_author=title.normalized_author,
            normalized_title=title.normalized_title,
            original_author=title.original_author,
            original_title=title.original_title,
            year=title.year,
            publisher=title.publisher,
            edition=title.edition,
            format=title.format,
            physical_availability=title.physical_availability,
            online_availability=title.online_availability,
            place=title.place,
            chapter=title.chapter,
            language=title.language,
            type_bib=title.type_bib,
        )
        self._session.add(orm)
        self._session.commit()
        title.id = orm.id
        return title

    def update(self, title: Title) -> None:
        orm = self._session.query(TituloORM).filter_by(id=title.id).first()
        if orm:
            orm.normalized_author = title.normalized_author
            orm.normalized_title = title.normalized_title
            orm.original_author = title.original_author
            orm.original_title = title.original_title
            orm.year = title.year
            orm.publisher = title.publisher
            orm.edition = title.edition
            orm.format = title.format
            orm.physical_availability = title.physical_availability
            orm.online_availability = title.online_availability
            orm.place = title.place
            orm.chapter = title.chapter
            orm.language = title.language
            orm.type_bib = title.type_bib
            self._session.commit()

    def link_to_subject(self, title: Title, subject: Subject) -> None:
        titulo_orm = self._session.query(TituloORM).filter_by(id=title.id).first()
        asignatura_orm = self._session.query(AsignaturaORM).filter_by(id=subject.id).first()
        if titulo_orm and asignatura_orm and asignatura_orm not in titulo_orm.asignaturas:
            titulo_orm.asignaturas.append(asignatura_orm)
            self._session.commit()

    def get_all_with_relations(self) -> List[Title]:
        return [_orm_to_title(o) for o in self._session.query(TituloORM).all()]


class SQLAlchemyAdquisicionRepository(AdquisicionRepositoryPort):
    """Repositorio de Adquisición usando SQLAlchemy."""

    def __init__(self, session=None):
        self._session = session or Sesion()

    def get_by_title(self, title_id: int) -> Optional[Acquisition]:
        orm = self._session.query(AdquisicionORM).filter_by(title_id=title_id).first()
        return _orm_to_acquisition(orm) if orm else None

    def save(self, acquisition: Acquisition) -> Acquisition:
        orm = AdquisicionORM(
            title_id=acquisition.title_id,
            status=acquisition.status,
            available_printed=acquisition.available_printed,
            available_digital=acquisition.available_digital,
        )
        self._session.add(orm)
        self._session.commit()
        acquisition.id = orm.id
        return acquisition

    def get_all_available(self) -> List[Acquisition]:
        orms = self._session.query(AdquisicionORM).filter_by(status='disponible').all()
        return [_orm_to_acquisition(o) for o in orms]
