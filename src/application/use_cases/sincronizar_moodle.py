from dataclasses import dataclass
from src.domain.events.datos_lms_sincronizados_event import DatosLmsSincronizadosEvent
from src.application.ports.out_.cursos_client_port import CursosClientPort
from src.application.ports.out_.event_publisher_port import EventPublisherPort
from src.application.ports.out_.lms_repository_port import LmsRepositoryPort
from src.application.ports.out_.moodle_api_port import MoodleApiPort
from src.application.ports.out_.recursos_client_port import RecursosClientPort
from src.application.ports.out_.trazabilidad_client_port import TrazabilidadClientPort


@dataclass
class SincronizarMoodleCommand:
    force: bool = False


class SincronizarMoodleUseCase:
    def __init__(
        self,
        moodle_api: MoodleApiPort,
        repo: LmsRepositoryPort,
        event_publisher: EventPublisherPort,
        trazabilidad: TrazabilidadClientPort,
        cursos_client: CursosClientPort,
        recursos_client: RecursosClientPort,
    ):
        self._moodle = moodle_api
        self._repo = repo
        self._event_publisher = event_publisher
        self._trazabilidad = trazabilidad
        self._cursos_client = cursos_client
        self._recursos_client = recursos_client

    async def execute(self, command: SincronizarMoodleCommand) -> dict:
        cursos = await self._moodle.get_courses()
        total = await self._repo.save_cursos(cursos)
        # Propaga el catálogo de cursos a ms-cursos-recursos (no bloqueante).
        await self._cursos_client.sync_cursos(cursos)
        todas_las_interacciones = []
        todas_las_actividades = []
        for curso in cursos:
            acts = await self._moodle.get_activities(curso.moodle_course_id)
            total += await self._repo.save_actividades(acts)
            todas_las_actividades.extend(acts)
            grades = await self._moodle.get_grades(curso.moodle_course_id)
            total += await self._repo.save_calificaciones(grades)
            events = await self._moodle.get_events(curso.moodle_course_id)
            total += await self._repo.save_interacciones(events)
            todas_las_interacciones.extend(events)
            vistas = await self._moodle.get_resource_views(curso.moodle_course_id)
            todas_las_interacciones.extend(vistas)
        self._event_publisher.publish(
            DatosLmsSincronizadosEvent(registros_procesados=total)
        )
        await self._trazabilidad.sync_interacciones(todas_las_interacciones)
        # Propaga las actividades como recursos a ms-cursos-recursos (no bloqueante).
        await self._recursos_client.sync_recursos(todas_las_actividades)
        return {"registros_procesados": total, "cursos": len(cursos)}
