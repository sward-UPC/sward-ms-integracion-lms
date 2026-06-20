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
            # Excluye el curso-sitio de Moodle (id 1 = portada, no es un curso real).
            for c in (data if isinstance(data, list) else [])
            if str(c.get("id")) != "1"
        ]

    async def get_activities(self, moodle_course_id: str) -> list[ActividadLMS]:
        data = await self._call("core_course_get_contents", courseid=moodle_course_id)
        acts = []
        for section in data if isinstance(data, list) else []:
            seccion = section.get("name", "") or ""
            for m in section.get("modules", []):
                acts.append(
                    ActividadLMS(
                        moodle_activity_id=str(m["id"]),
                        moodle_course_id=moodle_course_id,
                        nombre=m.get("name", ""),
                        tipo=m.get("modname", ""),
                        url=m.get("url", "") or "",
                        seccion=seccion,
                    )
                )
        return acts

    async def get_course_resources(self, moodle_course_id: str) -> list[dict]:
        """Lista TODOS los módulos del curso por sección, con tipo y URL.

        A diferencia de get_events (solo actividades calificadas), incluye
        lecturas/páginas/recursos (page, resource, url, book…), para poder
        sugerir material concreto de Moodle al reforzar una sección.
        """
        data = await self._call("core_course_get_contents", courseid=moodle_course_id)
        out: list[dict] = []
        for section in data if isinstance(data, list) else []:
            nombre = section.get("name", "") or ""
            for m in section.get("modules", []):
                if (m.get("modname", "") or "").lower() == "label":
                    continue  # las etiquetas no son recursos navegables
                out.append(
                    {
                        "seccion": nombre,
                        "nombre": m.get("name", "") or "",
                        "tipo": (m.get("modname", "") or "").lower(),
                        "url": m.get("url", "") or "",
                    }
                )
        return out

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
    ) -> dict[tuple[str, str], dict[str, str]]:
        """Mapa {(modname, instance): {"seccion", "url"}} para concepto y enlace.

        El concepto/skill de SAKT es la sección del curso; la url es el enlace
        directo al módulo en Moodle (core_course_get_contents lo devuelve).
        """
        data = await self._call("core_course_get_contents", courseid=moodle_course_id)
        mapa: dict[tuple[str, str], dict[str, str]] = {}
        for section in data if isinstance(data, list) else []:
            nombre = section.get("name", "") or "General"
            for m in section.get("modules", []):
                if m.get("modname") and m.get("instance") is not None:
                    mapa[(str(m["modname"]), str(m["instance"]))] = {
                        "seccion": nombre,
                        "url": m.get("url", "") or "",
                    }
        return mapa

    async def get_resource_views(self, moodle_course_id: str) -> list[InteraccionLMS]:
        """Interacciones tipo 'vista' de lecturas/recursos no calificados.

        Lee el estado de finalización ("completar al ver") por usuario y emite
        una InteraccionLMS por cada lectura COMPLETADA (es_vista=True, sin nota).
        """
        import asyncio

        LECTURA = {"page", "url", "resource", "book", "lesson", "folder"}
        try:
            contenidos = await self._call(
                "core_course_get_contents", courseid=moodle_course_id
            )
        except Exception:
            return []
        modmap: dict = {}
        for sec in contenidos if isinstance(contenidos, list) else []:
            seccion = sec.get("name", "") or ""
            for m in sec.get("modules", []):
                if (m.get("modname", "") or "").lower() in LECTURA:
                    modmap[m.get("id")] = {
                        "seccion": seccion,
                        "nombre": m.get("name", "") or "",
                        "tipo": (m.get("modname", "") or "").lower(),
                        "url": m.get("url", "") or "",
                        "instance": str(m.get("instance", "")),
                    }
        if not modmap:
            return []
        usuarios = await self._get_enrolled_users(moodle_course_id)
        sem = asyncio.Semaphore(8)

        async def _vistas_de(user):
            uid = user.get("id")
            if not uid:
                return []
            async with sem:
                try:
                    data = await self._call(
                        "core_completion_get_activities_completion_status",
                        courseid=moodle_course_id,
                        userid=uid,
                    )
                except Exception:
                    return []
            out = []
            for st in data.get("statuses", []) if isinstance(data, dict) else []:
                if st.get("state") not in (1, 2):
                    continue
                info = modmap.get(st.get("cmid"))
                if not info:
                    continue
                instancia = info["instance"] or str(st.get("cmid"))
                nombre = user.get("fullname") or " ".join(
                    filter(
                        None,
                        [user.get("firstname", ""), user.get("lastname", "")],
                    )
                )
                out.append(
                    InteraccionLMS(
                        moodle_event_id=f"vista-{uid}-{instancia}",
                        moodle_user_id=str(uid),
                        moodle_course_id=moodle_course_id,
                        moodle_activity_id=instancia,
                        nombre=nombre,
                        correo=user.get("email", ""),
                        concepto=info["seccion"],
                        url_modulo=info["url"],
                        nombre_actividad=info["nombre"],
                        tipo_recurso=info["tipo"],
                        accion="view",
                        es_correcta=True,
                        nota=0.0,
                        es_vista=True,
                    )
                )
            return out

        resultados = await asyncio.gather(*[_vistas_de(u) for u in usuarios])
        return [i for sub in resultados for i in sub]

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
                modinfo = secciones.get(
                    (str(item.get("itemmodule", "")), instancia), {}
                )
                # Concepto = sección del curso; si no se resuelve, el nombre del ítem.
                concepto = (
                    modinfo.get("seccion") or item.get("itemname", "") or "General"
                )
                # Nombre real de la actividad en Moodle (independiente de la sección).
                nombre_actividad = (item.get("itemname") or "").strip()
                # Tipo de módulo de Moodle (assign, quiz, page, url, resource, ...).
                tipo_recurso = (item.get("itemmodule") or "").strip().lower()
                results.append(
                    InteraccionLMS(
                        moodle_event_id=f"{user_id}-{instancia}",
                        moodle_user_id=str(user_id),
                        moodle_course_id=moodle_course_id,
                        moodle_activity_id=instancia,
                        nombre=nombre,
                        correo=correo,
                        concepto=concepto,
                        url_modulo=modinfo.get("url", ""),
                        nombre_actividad=nombre_actividad,
                        tipo_recurso=tipo_recurso,
                        accion="submit",
                        es_correcta=graderaw / grademax >= 0.5
                        if grademax > 0
                        else False,
                        nota=round(graderaw / grademax * 100, 1)
                        if grademax > 0
                        else 0.0,
                        fecha_evento=fecha,
                    )
                )
        return results
