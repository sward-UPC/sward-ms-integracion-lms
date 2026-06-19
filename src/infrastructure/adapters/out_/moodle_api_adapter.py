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

    async def buscar_por_correo(self, correo: str) -> dict | None:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"{settings.moodle_base_url}/webservice/rest/server.php",
                params={
                    "wstoken": settings.moodle_token,
                    "moodlewsrestformat": "json",
                    "wsfunction": "core_user_get_users",
                    "criteria[0][key]": "email",
                    "criteria[0][value]": correo,
                },
            )
            r.raise_for_status()
            data = r.json()

        users = data.get("users", []) if isinstance(data, dict) else []
        if not users:
            return None

        user = users[0]
        moodle_user_id: int = user["id"]

        # Determinar rol revisando los roles en los cursos del usuario.
        rol = "estudiante"
        ROLES_DOCENTE = {"editingteacher", "teacher", "manager", "coursecreator"}
        try:
            courses = await self._call(
                "core_enrol_get_users_courses", userid=moodle_user_id
            )
            for course in courses[:5] if isinstance(courses, list) else []:
                enrolled = await self._call(
                    "core_enrol_get_enrolled_users", courseid=course["id"]
                )
                for u in enrolled if isinstance(enrolled, list) else []:
                    if u.get("id") == moodle_user_id:
                        if any(
                            r.get("shortname") in ROLES_DOCENTE
                            for r in u.get("roles", [])
                        ):
                            rol = "docente"
                        break
                if rol == "docente":
                    break
        except Exception:
            pass  # rol queda como "estudiante" si Moodle falla en este paso

        return {
            "moodle_user_id": moodle_user_id,
            "nombre": user.get("firstname", ""),
            "apellido": user.get("lastname", ""),
            "correo": user.get("email", correo),
            "rol": rol,
        }

    async def _secciones_por_modulo(
        self, moodle_course_id: str
    ) -> dict[tuple[str, str], str]:
        """Mapa {(modname, instance): nombre_de_seccion} para asignar el concepto.

        El concepto/skill de SAKT es la sección del curso a la que pertenece la
        actividad (core_course_get_contents devuelve secciones con sus módulos).
        """
        data = await self._call("core_course_get_contents", courseid=moodle_course_id)
        mapa: dict[tuple[str, str], str] = {}
        for section in data if isinstance(data, list) else []:
            nombre = section.get("name", "") or "General"
            for m in section.get("modules", []):
                if m.get("modname") and m.get("instance") is not None:
                    mapa[(str(m["modname"]), str(m["instance"]))] = nombre
        return mapa

    async def get_events(self, moodle_course_id: str) -> list[InteraccionLMS]:
        users = await self._get_enrolled_users(moodle_course_id)
        secciones = await self._secciones_por_modulo(moodle_course_id)
        results = []
        for user in users:
            user_id = user.get("id")
            if not user_id:
                continue
            nombre = user.get("fullname") or " ".join(
                filter(None, [user.get("firstname", ""), user.get("lastname", "")])
            )
            correo = user.get("email", "")
            for item in await self._get_grade_items(moodle_course_id, user_id):
                graderaw = float(item["graderaw"])
                grademax = float(item.get("grademax") or 100.0)
                submitted_ts = item.get("gradedatesubmitted")
                fecha = (
                    datetime.fromtimestamp(submitted_ts, tz=timezone.utc)
                    if submitted_ts
                    else datetime.now(timezone.utc)
                )
                instancia = str(item.get("iteminstance", ""))
                # Concepto = sección del curso; si no se resuelve, el nombre del ítem.
                concepto = (
                    secciones.get((str(item.get("itemmodule", "")), instancia))
                    or item.get("itemname", "")
                    or "General"
                )
                results.append(
                    InteraccionLMS(
                        moodle_event_id=f"{user_id}-{instancia}",
                        moodle_user_id=str(user_id),
                        moodle_course_id=moodle_course_id,
                        moodle_activity_id=instancia,
                        nombre=nombre,
                        correo=correo,
                        concepto=concepto,
                        accion="submit",
                        es_correcta=graderaw / grademax >= 0.5
                        if grademax > 0
                        else False,
                        fecha_evento=fecha,
                    )
                )
        return results
