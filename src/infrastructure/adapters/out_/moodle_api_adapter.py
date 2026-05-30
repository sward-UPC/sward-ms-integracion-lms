import httpx
from src.domain.entities.actividad_lms import ActividadLMS
from src.domain.entities.calificacion_lms import CalificacionLMS
from src.domain.entities.curso_lms import CursoLMS
from src.domain.entities.interaccion_lms import InteraccionLMS
from src.domain.ports.out_.moodle_api_port import MoodleApiPort
from src.infrastructure.config.settings import settings


class MoodleApiAdapter(MoodleApiPort):
    async def _call(self, function: str, **params) -> list | dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                f"{settings.moodle_base_url}/webservice/rest/server.php",
                params={
                    "wstoken": settings.moodle_token,
                    "moodlewsrestformat": "json",
                    "wsfunction": function,
                    **params,
                },
            )
            r.raise_for_status()
            return r.json()

    async def get_courses(self) -> list[CursoLMS]:
        data = await self._call("core_course_get_courses")
        return [
            CursoLMS(
                moodle_course_id=str(c["id"]),
                nombre=c.get("fullname", ""),
                codigo=c.get("shortname", ""),
            )
            for c in (data if isinstance(data, list) else [])
        ]

    async def get_activities(self, moodle_course_id: str) -> list[ActividadLMS]:
        data = await self._call("core_course_get_contents", courseid=moodle_course_id)
        acts = []
        for section in data if isinstance(data, list) else []:
            for m in section.get("modules", []):
                acts.append(
                    ActividadLMS(
                        moodle_activity_id=str(m["id"]),
                        moodle_course_id=moodle_course_id,
                        nombre=m.get("name", ""),
                        tipo=m.get("modname", ""),
                    )
                )
        return acts

    async def get_grades(self, moodle_course_id: str) -> list[CalificacionLMS]:
        return []

    async def get_events(self, moodle_course_id: str) -> list[InteraccionLMS]:
        return []
