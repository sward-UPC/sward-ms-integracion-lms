from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field

from src.application.use_cases.buscar_usuario_moodle import BuscarUsuarioMoodleUseCase
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
from src.application.use_cases.consultar_recursos_curso_lms import (
    ConsultarRecursosCursoLmsUseCase,
)
from src.application.use_cases.sincronizar_moodle import (
    SincronizarMoodleCommand,
    SincronizarMoodleUseCase,
)
from src.infrastructure.dependencies import (
    get_buscar_usuario_moodle_uc,
    get_consultar_actividades_uc,
    get_consultar_calificaciones_uc,
    get_consultar_cursos_uc,
    get_consultar_interacciones_uc,
    get_consultar_recursos_curso_uc,
    get_sincronizar_moodle_uc,
    require_jwt,
    require_service_key,
)

# Endpoints de usuario — requieren JWT.
router = APIRouter(prefix="/lms", tags=["LMS"], dependencies=[Depends(require_jwt)])

# Endpoints internos — llamados por lambdas con X-Service-Key, no por usuarios.
internal_router = APIRouter(
    prefix="/lms",
    tags=["LMS — Internal"],
    dependencies=[Depends(require_service_key)],
)


class CursoLMSResponse(BaseModel):
    """Respuesta que contiene información de un curso del LMS."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "moodle_course_id": "5",
                "nombre": "Algoritmos y Estructuras de Datos",
                "codigo": "CS-2025-001",
            }
        },
    )

    id: str = Field(
        description="UUID único del curso en SWARD",
        example="550e8400-e29b-41d4-a716-446655440000",
    )
    moodle_course_id: str = Field(description="ID del curso en Moodle", example="5")
    nombre: str = Field(
        description="Nombre del curso",
        max_length=255,
        example="Algoritmos y Estructuras de Datos",
    )
    codigo: str = Field(
        description="Código interno del curso", max_length=50, example="CS-2025-001"
    )


class ActividadLMSResponse(BaseModel):
    """Respuesta que contiene información de una actividad del LMS."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "moodle_activity_id": "12",
                "nombre": "Quiz 1 - Recursión",
                "tipo": "quiz",
            }
        },
    )

    id: str = Field(
        description="UUID único de la actividad en SWARD",
        example="550e8400-e29b-41d4-a716-446655440001",
    )
    moodle_activity_id: str = Field(
        description="ID de la actividad en Moodle", example="12"
    )
    nombre: str = Field(
        description="Nombre de la actividad",
        max_length=255,
        example="Quiz 1 - Recursión",
    )
    tipo: str = Field(
        description="Tipo de actividad (quiz, assignment, etc.)",
        max_length=50,
        example="quiz",
    )


class CalificacionLMSResponse(BaseModel):
    """Respuesta que contiene información de una calificación del LMS."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "moodle_user_id": "123",
                "puntaje": 85.5,
                "puntaje_maximo": 100.0,
            }
        },
    )

    id: str = Field(
        description="UUID único de la calificación en SWARD",
        example="550e8400-e29b-41d4-a716-446655440002",
    )
    moodle_user_id: str = Field(description="ID del usuario en Moodle", example="123")
    puntaje: float = Field(description="Puntaje obtenido", ge=0, example=85.5)
    puntaje_maximo: float = Field(
        description="Puntaje máximo posible", ge=0, example=100.0
    )


class InteraccionLMSResponse(BaseModel):
    """Respuesta que contiene información de una interacción del LMS."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440003",
                "moodle_user_id": "123",
                "accion": "view",
                "es_correcta": True,
                "fecha": "2025-05-31T14:30:00Z",
            }
        },
    )

    id: str = Field(
        description="UUID única de la interacción en SWARD",
        example="550e8400-e29b-41d4-a716-446655440003",
    )
    moodle_user_id: str = Field(description="ID del usuario en Moodle", example="123")
    accion: str = Field(
        description="Tipo de acción realizada", max_length=50, example="view"
    )
    es_correcta: bool = Field(
        description="Indica si la acción fue correcta o no", example=True
    )
    fecha: str = Field(
        description="Fecha y hora de la interacción en ISO 8601",
        example="2025-05-31T14:30:00Z",
    )


class RecursoCursoResponse(BaseModel):
    """Recurso/módulo de un curso del LMS (por sección, con tipo y URL)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "seccion": "Semana 1-2: Fundamentos",
                "nombre": "Lectura: Introducción",
                "tipo": "page",
                "url": "https://moodle.example/mod/page/view.php?id=1",
            }
        },
    )

    seccion: str = Field(description="Sección del curso a la que pertenece el recurso")
    nombre: str = Field(description="Nombre del recurso/módulo en Moodle")
    tipo: str = Field(description="Tipo de módulo de Moodle (page, resource, url, ...)")
    url: str = Field(description="Enlace directo al recurso en Moodle")


class SyncResultResponse(BaseModel):
    """Respuesta que contiene el resultado de la sincronización."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "registros_procesados": 150,
                "cursos": 3,
            }
        },
    )

    registros_procesados: int = Field(
        description="Cantidad total de registros procesados",
        ge=0,
        example=150,
    )
    cursos: int = Field(description="Cantidad de cursos sincronizados", ge=0, example=3)


@router.get(
    "/courses",
    status_code=status.HTTP_200_OK,
    response_model=list[CursoLMSResponse],
    responses={
        200: {
            "description": "Lista de cursos obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "moodle_course_id": "5",
                            "nombre": "Algoritmos y Estructuras de Datos",
                            "codigo": "CS-2025-001",
                        }
                    ]
                }
            },
        },
        401: {"description": "No autorizado. JWT inválido o expirado."},
        500: {"description": "Error interno del servidor."},
    },
)
async def get_courses(uc: ConsultarCursosLmsUseCase = Depends(get_consultar_cursos_uc)):
    """Obtiene la lista de todos los cursos del LMS.

    **Flujo:** 1. Valida JWT 2. Consulta base de datos 3. Retorna lista de cursos

    **SLA:** <100ms | **Auth:** JWT | **Rate Limit:** 60 req/min
    """
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


@router.get(
    "/activities",
    status_code=status.HTTP_200_OK,
    response_model=list[ActividadLMSResponse],
    responses={
        200: {
            "description": "Lista de actividades obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440001",
                            "moodle_activity_id": "12",
                            "nombre": "Quiz 1 - Recursión",
                            "tipo": "quiz",
                        }
                    ]
                }
            },
        },
        401: {"description": "No autorizado. JWT inválido o expirado."},
        500: {"description": "Error interno del servidor."},
    },
)
async def get_activities(
    courseId: str | None = Query(
        default=None,
        max_length=64,
        description="ID del curso en Moodle para filtrar actividades",
        example="5",
    ),
    uc: ConsultarActividadesLmsUseCase = Depends(get_consultar_actividades_uc),
):
    """Obtiene la lista de actividades del LMS, opcionalmente filtradas por curso.

    **Flujo:** 1. Valida JWT 2. Filtra por courseId si se proporciona 3. Retorna lista de actividades

    **SLA:** <150ms | **Auth:** JWT | **Rate Limit:** 60 req/min
    """
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


@router.get(
    "/courses/{moodle_course_id}/resources",
    status_code=status.HTTP_200_OK,
    response_model=list[RecursoCursoResponse],
    responses={
        200: {"description": "Recursos del curso por sección (tipo + URL)"},
        401: {"description": "No autorizado. JWT inválido o expirado."},
        502: {"description": "El LMS (Moodle) no está disponible."},
    },
)
async def get_course_resources(
    moodle_course_id: str,
    uc: ConsultarRecursosCursoLmsUseCase = Depends(get_consultar_recursos_curso_uc),
):
    """Recursos/módulos del curso por sección, en vivo desde Moodle.

    Incluye lecturas/páginas (page, resource, url, book), no solo actividades
    calificadas, con su URL directa. Permite sugerir material concreto para
    reforzar una sección débil. **Auth:** JWT
    """
    recursos = await uc.execute(moodle_course_id)
    return [
        {
            "seccion": r.get("seccion", ""),
            "nombre": r.get("nombre", ""),
            "tipo": r.get("tipo", ""),
            "url": r.get("url", ""),
        }
        for r in recursos
    ]


@router.get(
    "/grades",
    status_code=status.HTTP_200_OK,
    response_model=list[CalificacionLMSResponse],
    responses={
        200: {
            "description": "Lista de calificaciones obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440002",
                            "moodle_user_id": "123",
                            "puntaje": 85.5,
                            "puntaje_maximo": 100.0,
                        }
                    ]
                }
            },
        },
        401: {"description": "No autorizado. JWT inválido o expirado."},
        500: {"description": "Error interno del servidor."},
    },
)
async def get_grades(
    courseId: str | None = Query(
        default=None,
        max_length=64,
        description="ID del curso en Moodle para filtrar calificaciones",
        example="5",
    ),
    userId: str | None = Query(
        default=None,
        max_length=64,
        description="ID del usuario en Moodle para filtrar calificaciones",
        example="123",
    ),
    uc: ConsultarCalificacionesLmsUseCase = Depends(get_consultar_calificaciones_uc),
):
    """Obtiene la lista de calificaciones del LMS, opcionalmente filtradas por curso y/o usuario.

    **Flujo:** 1. Valida JWT 2. Filtra por courseId y/o userId si se proporcionan 3. Retorna lista de calificaciones

    **SLA:** <200ms | **Auth:** JWT | **Rate Limit:** 60 req/min
    """
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


@router.get(
    "/interactions",
    status_code=status.HTTP_200_OK,
    response_model=list[InteraccionLMSResponse],
    responses={
        200: {
            "description": "Lista de interacciones obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440003",
                            "moodle_user_id": "123",
                            "accion": "view",
                            "es_correcta": True,
                            "fecha": "2025-05-31T14:30:00Z",
                        }
                    ]
                }
            },
        },
        401: {"description": "No autorizado. JWT inválido o expirado."},
        500: {"description": "Error interno del servidor."},
    },
)
async def get_interactions(
    courseId: str | None = Query(
        default=None,
        max_length=64,
        description="ID del curso en Moodle para filtrar interacciones",
        example="5",
    ),
    userId: str | None = Query(
        default=None,
        max_length=64,
        description="ID del usuario en Moodle para filtrar interacciones",
        example="123",
    ),
    uc: ConsultarInteraccionesLmsUseCase = Depends(get_consultar_interacciones_uc),
):
    """Obtiene la lista de interacciones del LMS, opcionalmente filtradas por curso y/o usuario.

    **Flujo:** 1. Valida JWT 2. Filtra por courseId y/o userId si se proporcionan 3. Retorna lista de interacciones

    **SLA:** <250ms | **Auth:** JWT | **Rate Limit:** 60 req/min
    """
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


class UsuarioMoodleResponse(BaseModel):
    """Datos del usuario encontrado en Moodle."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "moodle_user_id": 7,
                "nombre": "Juan",
                "apellido": "Pérez",
                "correo": "jperez@sward.edu",
                "rol": "estudiante",
            }
        },
    )

    moodle_user_id: int = Field(
        description="ID numérico del usuario en Moodle", example=7
    )
    nombre: str = Field(description="Nombre del usuario en Moodle", example="Juan")
    apellido: str = Field(description="Apellido del usuario en Moodle", example="Pérez")
    correo: str = Field(
        description="Correo electrónico institucional", example="jperez@sward.edu"
    )
    rol: str = Field(
        description="Rol detectado en Moodle: estudiante | docente",
        example="estudiante",
    )


@internal_router.get(
    "/users/lookup",
    status_code=status.HTTP_200_OK,
    response_model=UsuarioMoodleResponse,
    responses={
        200: {"description": "Usuario encontrado en Moodle"},
        404: {"description": "Correo no registrado en Moodle"},
        422: {"description": "Parámetro correo inválido"},
    },
)
async def lookup_usuario_moodle(
    correo: str = Query(..., description="Correo institucional a buscar en Moodle"),
    uc: BuscarUsuarioMoodleUseCase = Depends(get_buscar_usuario_moodle_uc),
):
    """Busca un usuario en Moodle por correo electrónico.

    Usado por ms-usuarios durante el registro para verificar la identidad y
    obtener el moodle_user_id y rol del nuevo usuario.

    **Auth:** X-Service-Key | **SLA:** <2s (depende de Moodle)
    """
    usuario = await uc.execute(correo)
    return {
        "moodle_user_id": usuario.moodle_user_id,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "correo": usuario.correo,
        "rol": usuario.rol,
    }


@internal_router.post(
    "/sync",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SyncResultResponse,
    responses={
        202: {
            "description": "Sincronización iniciada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "timestamp": "2025-05-31T14:30:00Z",
                        "records_processed": 150,
                    }
                }
            },
        },
        401: {"description": "No autorizado. JWT inválido o expirado."},
        500: {"description": "Error interno del servidor."},
    },
)
async def sync(uc: SincronizarMoodleUseCase = Depends(get_sincronizar_moodle_uc)):
    """Inicia la sincronización de datos desde el LMS (Moodle).

    **Flujo:** 1. Valida JWT 2. Encola tarea de sincronización 3. Retorna confirmación con estado

    **SLA:** <500ms (async) | **Auth:** JWT | **Rate Limit:** 10 req/min
    """
    return await uc.execute(SincronizarMoodleCommand())
