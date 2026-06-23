"""Schemas de respuesta de la sincronización con el LMS."""

from pydantic import BaseModel, ConfigDict, Field


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
