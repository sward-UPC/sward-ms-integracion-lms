"""El alta en Moodle desde el registro de SWARD.

Las garantías que aquí se comprueban son las que tenía el script externo al que
este caso de uso reemplaza: no recrear a quien ya existe, matricular en los dos
cursos del estudio, y no dejar a nadie a medio matricular si falta un curso.
"""

from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.buscar_usuario_moodle import UsuarioMoodle
from src.application.use_cases.provisionar_participante import (
    ProvisionarParticipanteCommand,
    ProvisionarParticipanteUseCase,
)
from src.domain.errors import CursoDeValidacionNoExisteError

CURSOS = ["SWARD-EST", "SWARD-MF"]


def _moodle_sin_el_usuario():
    moodle = AsyncMock()
    moodle.buscar_por_correo.return_value = None
    moodle.crear_usuario.return_value = {"moodle_user_id": 42, "username": "jperez"}
    moodle.buscar_curso_por_codigo.side_effect = lambda c: {
        "moodle_course_id": {"SWARD-EST": "7", "SWARD-MF": "8"}[c],
        "nombre": c,
        "codigo": c,
    }
    return moodle


@pytest.mark.asyncio
async def test_crea_la_cuenta_y_matricula_en_los_dos_cursos():
    moodle = _moodle_sin_el_usuario()
    uc = ProvisionarParticipanteUseCase(moodle, CURSOS)

    usuario = await uc.execute(
        ProvisionarParticipanteCommand(
            correo="JPerez@upc.edu.pe", nombres="Juan", apellidos="Pérez"
        )
    )

    assert isinstance(usuario, UsuarioMoodle)
    assert usuario.moodle_user_id == 42
    assert usuario.rol == "estudiante"
    # El correo se normaliza: Moodle distingue mayúsculas y quedarían dos cuentas.
    moodle.crear_usuario.assert_awaited_once_with("jperez@upc.edu.pe", "Juan", "Pérez")
    assert moodle.matricular.await_count == 2
    cursos_matriculados = {c.args[1] for c in moodle.matricular.await_args_list}
    assert cursos_matriculados == {"7", "8"}


@pytest.mark.asyncio
async def test_no_recrea_a_quien_ya_existe_pero_si_lo_matricula():
    """Idempotencia: un reintento, o alguien dado de alta antes con el script."""
    moodle = _moodle_sin_el_usuario()
    moodle.buscar_por_correo.return_value = {
        "moodle_user_id": 7,
        "nombre": "Ana",
        "apellido": "Torres",
        "rol": "estudiante",
    }
    uc = ProvisionarParticipanteUseCase(moodle, CURSOS)

    usuario = await uc.execute(
        ProvisionarParticipanteCommand(
            correo="atorres@upc.edu.pe", nombres="Ana", apellidos="Torres"
        )
    )

    moodle.crear_usuario.assert_not_awaited()
    assert usuario.moodle_user_id == 7
    # Se matricula igual: pudo crearse a mano y no estar en los cursos.
    assert moodle.matricular.await_count == 2


@pytest.mark.asyncio
async def test_el_docente_se_matricula_con_su_rol():
    moodle = _moodle_sin_el_usuario()
    uc = ProvisionarParticipanteUseCase(moodle, CURSOS)

    await uc.execute(
        ProvisionarParticipanteCommand(
            correo="prof@upc.edu.pe", nombres="Luis", apellidos="Gómez", rol="docente"
        )
    )

    assert {c.args[2] for c in moodle.matricular.await_args_list} == {"docente"}


@pytest.mark.asyncio
async def test_falla_si_falta_un_curso_de_la_validacion():
    """Mejor fallar que matricular a medias: media secuencia no sirve para reentrenar."""
    moodle = _moodle_sin_el_usuario()
    moodle.buscar_curso_por_codigo.side_effect = lambda c: (
        {"moodle_course_id": "7", "nombre": c, "codigo": c}
        if c == "SWARD-EST"
        else None
    )
    uc = ProvisionarParticipanteUseCase(moodle, CURSOS)

    with pytest.raises(CursoDeValidacionNoExisteError) as exc:
        await uc.execute(
            ProvisionarParticipanteCommand(
                correo="x@upc.edu.pe", nombres="X", apellidos="Y"
            )
        )
    assert exc.value.codigo == "SWARD-MF"


@pytest.mark.asyncio
async def test_el_rol_de_quien_ya_existe_manda_sobre_el_pedido():
    """Si Moodle dice que es docente, no se le degrada a estudiante al registrarse."""
    moodle = _moodle_sin_el_usuario()
    moodle.buscar_por_correo.return_value = {
        "moodle_user_id": 2,
        "nombre": "Luis",
        "apellido": "Gómez",
        "rol": "docente",
    }
    uc = ProvisionarParticipanteUseCase(moodle, CURSOS)

    usuario = await uc.execute(
        ProvisionarParticipanteCommand(
            correo="prof@upc.edu.pe",
            nombres="Luis",
            apellidos="Gómez",
            rol="estudiante",
        )
    )

    assert usuario.rol == "docente"
    assert {c.args[2] for c in moodle.matricular.await_args_list} == {"docente"}
