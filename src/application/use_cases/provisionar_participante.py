"""Da de alta en Moodle a quien se registra en SWARD.

Hasta el 24 de septiembre este paso lo hacía un script externo (`crear_participantes.py`)
alimentado por un formulario de Google: alguien exportaba un CSV y lo corría a mano.
El registro de SWARD sólo admitía a quien ya existía en Moodle, de modo que el
sistema no podía incorporar a un participante por sí mismo.

Este caso de uso traslada esa responsabilidad al propio sistema, conservando las
garantías que tenía el script: es idempotente, no fija contraseñas y matricula en
los cursos de la validación con el rol que corresponde.
"""

import logging
from dataclasses import dataclass

from src.application.ports.out_.moodle_api_port import MoodleApiPort
from src.application.use_cases.buscar_usuario_moodle import UsuarioMoodle
from src.domain.errors import CursoDeValidacionNoExisteError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProvisionarParticipanteCommand:
    correo: str
    nombres: str
    apellidos: str
    rol: str = "estudiante"


class ProvisionarParticipanteUseCase:
    """Crea la cuenta en Moodle si hace falta y matricula en los cursos del estudio."""

    def __init__(self, moodle_api: MoodleApiPort, cursos: list[str]):
        self._moodle = moodle_api
        self._cursos = [c.strip() for c in cursos if c.strip()]

    async def execute(self, cmd: ProvisionarParticipanteCommand) -> UsuarioMoodle:
        correo = cmd.correo.strip().lower()

        # Idempotencia: quien ya existe en Moodle no se vuelve a crear. Puede
        # llegar aquí por un reintento, o porque se le dio de alta antes con el
        # script, y en los dos casos la respuesta debe ser la misma.
        existente = await self._moodle.buscar_por_correo(correo)
        if existente is not None:
            logger.info("El participante %s ya existía en Moodle; no se recrea", correo)
            usuario_id = int(existente["moodle_user_id"])
            rol = existente.get("rol", cmd.rol)
            nombres = existente.get("nombre", cmd.nombres)
            apellidos = existente.get("apellido", cmd.apellidos)
        else:
            creado = await self._moodle.crear_usuario(
                correo, cmd.nombres, cmd.apellidos
            )
            usuario_id = int(creado["moodle_user_id"])
            rol, nombres, apellidos = cmd.rol, cmd.nombres, cmd.apellidos

        # Matricular siempre, exista o no la cuenta: alguien creado a mano puede
        # no estar en los cursos, y enrol_manual_enrol_users no duplica.
        for codigo in self._cursos:
            curso = await self._moodle.buscar_curso_por_codigo(codigo)
            if curso is None:
                raise CursoDeValidacionNoExisteError(codigo)
            await self._moodle.matricular(usuario_id, curso["moodle_course_id"], rol)

        logger.info(
            "Participante %s provisionado (id %s, rol %s) en %d curso(s)",
            correo,
            usuario_id,
            rol,
            len(self._cursos),
        )
        return UsuarioMoodle(
            moodle_user_id=usuario_id,
            nombre=nombres,
            apellido=apellidos,
            correo=correo,
            rol=rol,
        )
