from abc import ABC, abstractmethod
from src.domain.entities.curso_lms import CursoLMS
from src.domain.entities.actividad_lms import ActividadLMS
from src.domain.entities.calificacion_lms import CalificacionLMS
from src.domain.entities.interaccion_lms import InteraccionLMS


class LmsRepositoryPort(ABC):
    @abstractmethod
    async def save_cursos(self, cursos: list[CursoLMS]) -> int: ...
    @abstractmethod
    async def find_cursos(self) -> list[CursoLMS]: ...
    @abstractmethod
    async def save_actividades(self, actividades: list[ActividadLMS]) -> int: ...
    @abstractmethod
    async def find_actividades(
        self, moodle_course_id: str | None = None
    ) -> list[ActividadLMS]: ...
    @abstractmethod
    async def save_calificaciones(
        self, calificaciones: list[CalificacionLMS]
    ) -> int: ...
    @abstractmethod
    async def find_calificaciones(
        self, moodle_course_id: str | None = None, moodle_user_id: str | None = None
    ) -> list[CalificacionLMS]: ...
    @abstractmethod
    async def save_interacciones(self, interacciones: list[InteraccionLMS]) -> int: ...
    @abstractmethod
    async def find_interacciones(
        self, moodle_course_id: str | None = None, moodle_user_id: str | None = None
    ) -> list[InteraccionLMS]: ...
