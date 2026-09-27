"""Lleva a Moodle la contraseña que la persona acaba de cambiar en SWARD.

Desde el 27 de septiembre de 2026 el participante elige **una sola contraseña**
al inscribirse y le sirve en los dos sitios. El alta la copia una vez, y con eso
solo, la promesa duraba hasta el primer cambio: quien la cambiaba en SWARD
seguía entrando al aula virtual con la anterior, sin que nada se lo dijera. Lo
encontró el tesista cambiando la suya.

Se busca por correo, no por identificador: es el dato que SWARD tiene a mano y el
que la persona reconoce. Si no existe en Moodle no es un error —puede ser una
cuenta creada antes de que el registro provisionara—, así que se informa y no se
rompe el cambio en SWARD.
"""

import logging
from dataclasses import dataclass

from src.application.ports.out_.moodle_api_port import MoodleApiPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CambiarPasswordMoodleCommand:
    correo: str
    password: str


class CambiarPasswordMoodleUseCase:
    def __init__(self, moodle_api: MoodleApiPort):
        self._moodle = moodle_api

    async def execute(self, cmd: CambiarPasswordMoodleCommand) -> bool:
        """Devuelve True si la cambió, False si esa persona no está en Moodle."""
        correo = cmd.correo.strip().lower()
        usuario = await self._moodle.buscar_por_correo(correo)
        if usuario is None:
            logger.info("Sin cuenta en Moodle para %s: no hay nada que cambiar", correo)
            return False
        await self._moodle.cambiar_password(
            int(usuario["moodle_user_id"]), cmd.password
        )
        return True
