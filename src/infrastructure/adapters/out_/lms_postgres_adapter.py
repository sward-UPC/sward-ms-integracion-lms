from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.actividad_lms import ActividadLMS
from src.domain.entities.calificacion_lms import CalificacionLMS
from src.domain.entities.curso_lms import CursoLMS
from src.domain.entities.interaccion_lms import InteraccionLMS
from src.application.ports.out_.lms_repository_port import LmsRepositoryPort
from src.infrastructure.db.models.lms_models import (
    ActividadLmsModel,
    CalificacionLmsModel,
    CursoLmsModel,
    InteraccionLmsModel,
)


class LmsPostgresAdapter(LmsRepositoryPort):
    def __init__(self, session: AsyncSession):
        self._s = session

    async def save_cursos(self, cursos: list[CursoLMS]) -> int:
        count = 0
        for c in cursos:
            existing = (
                await self._s.execute(
                    select(CursoLmsModel).where(
                        CursoLmsModel.moodle_course_id == c.moodle_course_id
                    )
                )
            ).scalar_one_or_none()
            if not existing:
                self._s.add(
                    CursoLmsModel(
                        id=c.id,
                        moodle_course_id=c.moodle_course_id,
                        nombre=c.nombre,
                        codigo=c.codigo,
                    )
                )
                count += 1
        await self._s.flush()
        return count

    async def find_cursos(self) -> list[CursoLMS]:
        r = await self._s.execute(select(CursoLmsModel))
        return [
            CursoLMS(
                id=m.id,
                moodle_course_id=m.moodle_course_id,
                nombre=m.nombre,
                codigo=m.codigo,
            )
            for m in r.scalars().all()
        ]

    async def save_actividades(self, actividades: list[ActividadLMS]) -> int:
        count = 0
        for a in actividades:
            if not (
                await self._s.execute(
                    select(ActividadLmsModel).where(
                        ActividadLmsModel.moodle_activity_id == a.moodle_activity_id
                    )
                )
            ).scalar_one_or_none():
                self._s.add(
                    ActividadLmsModel(
                        id=a.id,
                        moodle_activity_id=a.moodle_activity_id,
                        moodle_course_id=a.moodle_course_id,
                        nombre=a.nombre,
                        tipo=a.tipo,
                    )
                )
                count += 1
        await self._s.flush()
        return count

    async def find_actividades(
        self, moodle_course_id: str | None = None
    ) -> list[ActividadLMS]:
        q = select(ActividadLmsModel)
        if moodle_course_id:
            q = q.where(ActividadLmsModel.moodle_course_id == moodle_course_id)
        r = await self._s.execute(q)
        return [
            ActividadLMS(
                id=m.id,
                moodle_activity_id=m.moodle_activity_id,
                moodle_course_id=m.moodle_course_id,
                nombre=m.nombre,
                tipo=m.tipo,
            )
            for m in r.scalars().all()
        ]

    async def save_calificaciones(self, calificaciones: list[CalificacionLMS]) -> int:
        for c in calificaciones:
            self._s.add(
                CalificacionLmsModel(
                    id=c.id,
                    moodle_user_id=c.moodle_user_id,
                    moodle_activity_id=c.moodle_activity_id,
                    moodle_course_id=c.moodle_course_id,
                    puntaje=c.puntaje,
                    puntaje_maximo=c.puntaje_maximo,
                    fecha=c.fecha,
                )
            )
        await self._s.flush()
        return len(calificaciones)

    async def find_calificaciones(
        self, moodle_course_id=None, moodle_user_id=None
    ) -> list[CalificacionLMS]:
        q = select(CalificacionLmsModel)
        if moodle_course_id:
            q = q.where(CalificacionLmsModel.moodle_course_id == moodle_course_id)
        if moodle_user_id:
            q = q.where(CalificacionLmsModel.moodle_user_id == moodle_user_id)
        r = await self._s.execute(q)
        return [
            CalificacionLMS(
                id=m.id,
                moodle_user_id=m.moodle_user_id,
                moodle_activity_id=m.moodle_activity_id,
                moodle_course_id=m.moodle_course_id,
                puntaje=m.puntaje,
                puntaje_maximo=m.puntaje_maximo,
                fecha=m.fecha,
            )
            for m in r.scalars().all()
        ]

    async def save_interacciones(self, interacciones: list[InteraccionLMS]) -> int:
        for i in interacciones:
            self._s.add(
                InteraccionLmsModel(
                    id=i.id,
                    moodle_event_id=i.moodle_event_id or None,
                    moodle_user_id=i.moodle_user_id,
                    moodle_course_id=i.moodle_course_id,
                    moodle_activity_id=i.moodle_activity_id or None,
                    accion=i.accion,
                    es_correcta=i.es_correcta,
                    fecha_evento=i.fecha_evento,
                )
            )
        await self._s.flush()
        return len(interacciones)

    async def find_interacciones(
        self, moodle_course_id=None, moodle_user_id=None
    ) -> list[InteraccionLMS]:
        q = select(InteraccionLmsModel)
        if moodle_course_id:
            q = q.where(InteraccionLmsModel.moodle_course_id == moodle_course_id)
        if moodle_user_id:
            q = q.where(InteraccionLmsModel.moodle_user_id == moodle_user_id)
        r = await self._s.execute(q)
        return [
            InteraccionLMS(
                id=m.id,
                moodle_event_id=m.moodle_event_id or "",
                moodle_user_id=m.moodle_user_id,
                moodle_course_id=m.moodle_course_id,
                moodle_activity_id=m.moodle_activity_id or "",
                accion=m.accion,
                es_correcta=m.es_correcta,
                fecha_evento=m.fecha_evento,
            )
            for m in r.scalars().all()
        ]
