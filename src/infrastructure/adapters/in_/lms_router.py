from fastapi import APIRouter, Depends, Query

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
from src.infrastructure.dependencies import (
    get_consultar_actividades_uc,
    get_consultar_calificaciones_uc,
    get_consultar_cursos_uc,
    get_consultar_interacciones_uc,
    get_sincronizar_moodle_uc,
    require_jwt,
)

# Todos los endpoints de /lms exigen un JWT de acceso válido.
router = APIRouter(prefix="/lms", tags=["LMS"], dependencies=[Depends(require_jwt)])


@router.get("/courses")
async def get_courses(uc: ConsultarCursosLmsUseCase = Depends(get_consultar_cursos_uc)):
    cursos = await uc.execute()
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
    courseId: str | None = Query(default=None, max_length=64),
    uc: ConsultarActividadesLmsUseCase = Depends(get_consultar_actividades_uc),
):
    acts = await uc.execute(courseId)
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
    courseId: str | None = Query(default=None, max_length=64),
    userId: str | None = Query(default=None, max_length=64),
    uc: ConsultarCalificacionesLmsUseCase = Depends(get_consultar_calificaciones_uc),
):
    grades = await uc.execute(courseId, userId)
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
    courseId: str | None = Query(default=None, max_length=64),
    userId: str | None = Query(default=None, max_length=64),
    uc: ConsultarInteraccionesLmsUseCase = Depends(get_consultar_interacciones_uc),
):
    items = await uc.execute(courseId, userId)
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
async def sync(uc: SincronizarMoodleUseCase = Depends(get_sincronizar_moodle_uc)):
    return await uc.execute(SincronizarMoodleCommand())
