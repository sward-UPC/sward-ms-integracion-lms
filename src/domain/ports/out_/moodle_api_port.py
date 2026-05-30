from abc import ABC, abstractmethod
from src.domain.entities.actividad_lms import ActividadLMS
from src.domain.entities.calificacion_lms import CalificacionLMS
from src.domain.entities.curso_lms import CursoLMS
from src.domain.entities.interaccion_lms import InteraccionLMS


class MoodleApiPort(ABC):
    @abstractmethod
    async def get_courses(self) -> list[CursoLMS]: ...
    @abstractmethod
    async def get_activities(self, moodle_course_id: str) -> list[ActividadLMS]: ...
    @abstractmethod
    async def get_grades(self, moodle_course_id: str) -> list[CalificacionLMS]: ...
    @abstractmethod
    async def get_events(self, moodle_course_id: str) -> list[InteraccionLMS]: ...
