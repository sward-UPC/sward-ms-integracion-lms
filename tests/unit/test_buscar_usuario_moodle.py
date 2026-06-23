import pytest
from unittest.mock import AsyncMock

from src.application.use_cases.buscar_usuario_moodle import (
    BuscarUsuarioMoodleUseCase,
    UsuarioMoodle,
)
from src.domain.errors import UsuarioMoodleNoEncontradoError


@pytest.mark.asyncio
async def test_devuelve_usuario_plano_cuando_existe():
    moodle = AsyncMock()
    moodle.buscar_por_correo.return_value = {
        "moodle_user_id": 7,
        "nombre": "Juan",
        "apellido": "Pérez",
        "correo": "jperez@sward.edu",
        "rol": "docente",
    }
    uc = BuscarUsuarioMoodleUseCase(moodle)

    usuario = await uc.execute("jperez@sward.edu")

    assert isinstance(usuario, UsuarioMoodle)
    assert usuario.moodle_user_id == 7
    assert usuario.rol == "docente"


@pytest.mark.asyncio
async def test_lanza_error_de_dominio_cuando_no_existe():
    moodle = AsyncMock()
    moodle.buscar_por_correo.return_value = None
    uc = BuscarUsuarioMoodleUseCase(moodle)

    with pytest.raises(UsuarioMoodleNoEncontradoError):
        await uc.execute("nadie@sward.edu")
