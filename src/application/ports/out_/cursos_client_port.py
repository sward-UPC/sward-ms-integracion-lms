from abc import ABC, abstractmethod

from src.domain.entities.curso_lms import CursoLMS


class CursosClientPort(ABC):
    """Propaga los cursos sincronizados de Moodle al catálogo (ms-cursos-recursos)."""

    @abstractmethod
    async def sync_cursos(self, cursos: list[CursoLMS]) -> None: ...
