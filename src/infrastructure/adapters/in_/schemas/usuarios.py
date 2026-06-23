"""Schemas de respuesta relacionados con usuarios de Moodle."""

from pydantic import BaseModel, ConfigDict, Field


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
