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
                "password": "········",
                "rol": "estudiante",
            }
        },
    )

    correo: EmailStr = Field(..., description="Correo con el que se registró en SWARD")
    nombres: str = Field(..., min_length=1, max_length=100)
    apellidos: str = Field(..., min_length=1, max_length=100)
    # La contraseña que la persona eligió en SWARD, para que le sirva también en
    # el aula virtual y no tenga que manejar dos. Sólo se usa al crear la cuenta.
    # El ejemplo va oculto a propósito: la documentación de la API es pública
    # dentro del despliegue y no debe sugerir contraseñas reales.
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Contraseña elegida en SWARD. Se fija en Moodle al crear la cuenta.",
    )
    rol: Literal["estudiante", "docente"] = Field(
        default="estudiante",
        description="Rol con el que se matricula en los cursos de la validación",
    )


class CambiarPasswordRequest(BaseModel):
    """Cambio de contraseña pedido por SWARD, para que el aula virtual no se
    quede con la anterior."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {"correo": "jperez@upc.edu.pe", "password": "········"}
        },
    )

    correo: EmailStr = Field(..., description="Correo de quien cambió su contraseña")
    password: str = Field(..., min_length=8, max_length=128)
