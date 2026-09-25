"""Schemas de respuesta relacionados con usuarios de Moodle."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class ProvisionarParticipanteRequest(BaseModel):
    """Alta de un participante en Moodle pedida por el registro de SWARD."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "correo": "jperez@upc.edu.pe",
                "nombres": "Juan",
                "apellidos": "Pérez",
                "rol": "estudiante",
            }
        },
    )

    correo: EmailStr = Field(..., description="Correo con el que se registró en SWARD")
    nombres: str = Field(..., min_length=1, max_length=100)
    apellidos: str = Field(..., min_length=1, max_length=100)
    rol: Literal["estudiante", "docente"] = Field(
        default="estudiante",
        description="Rol con el que se matricula en los cursos de la validación",
    )
