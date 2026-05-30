from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.use_cases.consultar_actividades_lms import (
    ConsultarActividadesLmsUseCase,
)
from src.application.use_cases.consultar_calificaciones_lms import (
    ConsultarCalificacionesLmsUseCase,
)
from src.application.use_cases.consultar_cursos_lms import ConsultarCursosLmsUseCase
from src.application.use_cases.consultar_interacciones_lms import (
    ConsultarInteraccionesLmsUseCase,
)
from src.application.use_cases.sincronizar_moodle import (
    SincronizarMoodleCommand,
    SincronizarMoodleUseCase,
)
from src.infrastructure.adapters.out_.eventbridge_adapter import EventBridgeAdapter
from src.infrastructure.adapters.out_.lms_postgres_adapter import LmsPostgresAdapter
from src.infrastructure.adapters.out_.mock_moodle_api_adapter import (
    MockMoodleApiAdapter,
)
from src.infrastructure.adapters.out_.moodle_api_adapter import MoodleApiAdapter
from src.infrastructure.config.settings import settings
from src.infrastructure.db.database import get_session

router = APIRouter(prefix="/lms", tags=["LMS"])


def _moodle():
    return MockMoodleApiAdapter() if settings.moodle_mock else MoodleApiAdapter()


@router.get("/courses")
async def get_courses(session: AsyncSession = Depends(get_session)):
    cursos = await ConsultarCursosLmsUseCase(LmsPostgresAdapter(session)).execute()
    return [
        {
            "id": str(c.id),
            "moodle_course_id": c.moodle_course_id,
            "nombre": c.nombre,
            "codigo": c.codigo,
        }
        for c in cursos
    ]


@router.get("/activities")
async def get_activities(
    courseId: str | None = None, session: AsyncSession = Depends(get_session)
):
    acts = await ConsultarActividadesLmsUseCase(LmsPostgresAdapter(session)).execute(
        courseId
    )
    return [
        {
            "id": str(a.id),
            "moodle_activity_id": a.moodle_activity_id,
            "nombre": a.nombre,
            "tipo": a.tipo,
        }
        for a in acts
    ]


@router.get("/grades")
async def get_grades(
    courseId: str | None = None,
    userId: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    grades = await ConsultarCalificacionesLmsUseCase(
        LmsPostgresAdapter(session)
    ).execute(courseId, userId)
    return [
        {
            "id": str(g.id),
            "moodle_user_id": g.moodle_user_id,
            "puntaje": g.puntaje,
            "puntaje_maximo": g.puntaje_maximo,
        }
        for g in grades
    ]


@router.get("/interactions")
async def get_interactions(
    courseId: str | None = None,
    userId: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    items = await ConsultarInteraccionesLmsUseCase(LmsPostgresAdapter(session)).execute(
        courseId, userId
    )
    return [
        {
            "id": str(i.id),
            "moodle_user_id": i.moodle_user_id,
            "accion": i.accion,
            "es_correcta": i.es_correcta,
            "fecha": i.fecha_evento.isoformat(),
        }
        for i in items
    ]


@router.post("/sync")
async def sync(session: AsyncSession = Depends(get_session)):
    return await SincronizarMoodleUseCase(
        _moodle(), LmsPostgresAdapter(session), EventBridgeAdapter()
    ).execute(SincronizarMoodleCommand())
