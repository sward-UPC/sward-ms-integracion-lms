from datetime import datetime, timezone

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

    async def _get_enrolled_users(self, moodle_course_id: str) -> list[dict]:
        data = await self._call(
            "core_enrol_get_enrolled_users", courseid=moodle_course_id
        )
        return data if isinstance(data, list) else []

    async def _get_grade_items(self, moodle_course_id: str, user_id: int) -> list[dict]:
        data = await self._call(
            "gradereport_user_get_grade_items",
            courseid=moodle_course_id,
            userid=user_id,
        )
        items = []
        for ug in data.get("usergrades", []):
            for item in ug.get("gradeitems", []):
                if item.get("graderaw") is None:
                    continue
                if item.get("itemtype") != "mod":
                    continue
                items.append(item)
        return items

    async def get_grades(self, moodle_course_id: str) -> list[CalificacionLMS]:
        users = await self._get_enrolled_users(moodle_course_id)
        results = []
        for user in users:
            user_id = user.get("id")
            if not user_id:
                continue
            for item in await self._get_grade_items(moodle_course_id, user_id):
                results.append(
                    CalificacionLMS(
                        moodle_user_id=str(user_id),
                        moodle_activity_id=str(item.get("iteminstance", "")),
                        moodle_course_id=moodle_course_id,
                        puntaje=float(item["graderaw"]),
                        puntaje_maximo=float(item.get("grademax") or 100.0),
                    )
                )
        return results

    async def get_events(self, moodle_course_id: str) -> list[InteraccionLMS]:
        users = await self._get_enrolled_users(moodle_course_id)
        results = []
        for user in users:
            user_id = user.get("id")
            if not user_id:
                continue
            for item in await self._get_grade_items(moodle_course_id, user_id):
                graderaw = float(item["graderaw"])
                grademax = float(item.get("grademax") or 100.0)
                submitted_ts = item.get("gradedatesubmitted")
                fecha = (
                    datetime.fromtimestamp(submitted_ts, tz=timezone.utc)
                    if submitted_ts
                    else datetime.now(timezone.utc)
                )
                results.append(
                    InteraccionLMS(
                        moodle_event_id=f"{user_id}-{item.get('iteminstance', '')}",
                        moodle_user_id=str(user_id),
                        moodle_course_id=moodle_course_id,
                        moodle_activity_id=str(item.get("iteminstance", "")),
                        accion="submit",
                        es_correcta=graderaw / grademax >= 0.5
                        if grademax > 0
                        else False,
                        fecha_evento=fecha,
                    )
                )
        return results
