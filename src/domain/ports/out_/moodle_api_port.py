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
    @abstractmethod
    async def get_course_resources(self, moodle_course_id: str) -> list[dict]:
        """Módulos del curso por sección (lecturas/recursos incluidos).

        Retorna list[dict] con seccion, nombre, tipo (modname Moodle) y url.
        """
        ...

    @abstractmethod
    async def buscar_por_correo(self, correo: str) -> dict | None:
        """Busca un usuario en Moodle por correo electrónico.

        Retorna dict con moodle_user_id, nombre, apellido, correo, rol
        (estudiante | docente) o None si no existe.
        """
        ...
