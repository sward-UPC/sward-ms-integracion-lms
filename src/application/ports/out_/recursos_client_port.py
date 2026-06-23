from abc import ABC, abstractmethod

from src.domain.entities.actividad_lms import ActividadLMS


class RecursosClientPort(ABC):
    """Propaga las actividades de Moodle como recursos (ms-cursos-recursos)."""

    @abstractmethod
    async def sync_recursos(self, actividades: list[ActividadLMS]) -> None: ...
