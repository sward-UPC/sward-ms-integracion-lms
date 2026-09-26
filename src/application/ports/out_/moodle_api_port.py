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
    async def get_resource_views(self, moodle_course_id: str) -> list[InteraccionLMS]:
        """Interacciones tipo 'vista' de lecturas/recursos no calificados.

        Retorna InteraccionLMS con es_vista=True (sin nota), para alimentar
        el motor de preferencias por formato.
        """
        ...

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

    # ---------------------------------------------------------------- escritura
    # Hasta la versión del 24 de septiembre este puerto sólo leía. Crear la cuenta
    # en Moodle era tarea de un script externo alimentado por un formulario, de
    # modo que el registro de SWARD sólo funcionaba para quien ya existía allá.
    # Con estas tres operaciones el propio sistema da de alta al participante.

    @abstractmethod
    async def crear_usuario(self, correo: str, nombres: str, apellidos: str) -> dict:
        """Crea el usuario en Moodle y devuelve `{moodle_user_id, username}`.

        La contraseña no se fija aquí: Moodle genera una y se la envía a la
        persona, que debe cambiarla al entrar. Así nadie —tampoco el equipo de
        tesis— llega a conocerla.
        """
        ...

    @abstractmethod
    async def buscar_curso_por_codigo(self, codigo: str) -> dict | None:
        """Busca un curso por su nombre corto (`shortname`).

        Retorna `{moodle_course_id, nombre, codigo}` o None si no existe.
        """
        ...

    @abstractmethod
    async def matricular(self, moodle_user_id: int, moodle_course_id: str, rol: str) -> None:
        """Matricula al usuario en el curso con el rol indicado.

        `rol` es «estudiante» o «docente». Es idempotente: matricular a quien ya
        está matriculado no falla ni duplica.
        """
        ...
