from dataclasses import dataclass

from src.domain.errors import UsuarioMoodleNoEncontradoError
from src.application.ports.out_.moodle_api_port import MoodleApiPort


@dataclass
class UsuarioMoodle:
    """Datos planos del usuario tal como los expone Moodle al registro de SWARD."""

    moodle_user_id: int
    nombre: str
    apellido: str
    correo: str
    rol: str


class BuscarUsuarioMoodleUseCase:
    """Busca un usuario en Moodle por correo (usado por ms-usuarios en el registro)."""

    def __init__(self, moodle_api: MoodleApiPort):
        self._moodle = moodle_api

    async def execute(self, correo: str) -> UsuarioMoodle:
        usuario = await self._moodle.buscar_por_correo(correo)
        if usuario is None:
            raise UsuarioMoodleNoEncontradoError(correo)
        return UsuarioMoodle(
            moodle_user_id=usuario["moodle_user_id"],
            nombre=usuario.get("nombre", ""),
            apellido=usuario.get("apellido", ""),
            correo=usuario.get("correo", correo),
            rol=usuario.get("rol", "estudiante"),
        )
