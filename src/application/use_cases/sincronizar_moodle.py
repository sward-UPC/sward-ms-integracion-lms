from dataclasses import dataclass
from src.domain.events.datos_lms_sincronizados_event import DatosLmsSincronizadosEvent
from src.domain.ports.out_.event_publisher_port import EventPublisherPort
from src.domain.ports.out_.lms_repository_port import LmsRepositoryPort
from src.domain.ports.out_.moodle_api_port import MoodleApiPort


@dataclass
class SincronizarMoodleCommand:
    force: bool = False


class SincronizarMoodleUseCase:
    def __init__(
        self,
        moodle_api: MoodleApiPort,
        repo: LmsRepositoryPort,
        event_publisher: EventPublisherPort,
    ):
        self._moodle = moodle_api
        self._repo = repo
        self._event_publisher = event_publisher

    async def execute(self, command: SincronizarMoodleCommand) -> dict:
        cursos = await self._moodle.get_courses()
        total = await self._repo.save_cursos(cursos)
        for curso in cursos:
            acts = await self._moodle.get_activities(curso.moodle_course_id)
            total += await self._repo.save_actividades(acts)
            grades = await self._moodle.get_grades(curso.moodle_course_id)
            total += await self._repo.save_calificaciones(grades)
            events = await self._moodle.get_events(curso.moodle_course_id)
            total += await self._repo.save_interacciones(events)
        self._event_publisher.publish(
            DatosLmsSincronizadosEvent(registros_procesados=total)
        )
        return {"registros_procesados": total, "cursos": len(cursos)}
