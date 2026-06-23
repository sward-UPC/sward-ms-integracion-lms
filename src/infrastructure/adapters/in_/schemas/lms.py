"""Schemas de respuesta de los datos del LMS (cursos, actividades, etc.).

Contratos Pydantic de salida del adaptador HTTP. Calzan exactamente con el JSON
que arman las rutas, sin alterar la forma de la respuesta.
"""

from pydantic import BaseModel, ConfigDict, Field


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
