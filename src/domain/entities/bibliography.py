"""
Entidades de dominio puras: BibliographyEntry
Representa una entrada bibliográfica extraída de un documento.
No depende de ninguna tecnología de infraestructura.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BibliographyType(str, Enum):
    BASIC = 'basic'
    COMPLEMENTARY = 'complementary'


@dataclass
class BibliographyEntry:
    """Una entrada bibliográfica cruda extraída de un documento."""
    author: str
    title: str
    year: Optional[str] = None
    publisher: Optional[str] = None
    url: Optional[str] = None
    chapter_title: Optional[str] = None
    type: str = 'book'        # 'book' o 'article'
    bib_type: str = 'basic'   # 'basic' o 'complementary'
    normalized_author: Optional[str] = None
    normalized_title: Optional[str] = None
    language: Optional[str] = 'Español'

    @property
    def is_article(self) -> bool:
        return self.type == 'article' or self.url is not None
