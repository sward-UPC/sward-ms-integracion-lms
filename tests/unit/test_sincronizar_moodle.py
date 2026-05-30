import pytest
from unittest.mock import AsyncMock, MagicMock
from src.application.use_cases.sincronizar_moodle import (
    SincronizarMoodleCommand,
    SincronizarMoodleUseCase,
)
from src.domain.entities.curso_lms import CursoLMS


@pytest.fixture
def use_case():
    moodle = AsyncMock()
    moodle.get_courses.return_value = [
        CursoLMS(moodle_course_id="c1", nombre="Algoritmos")
    ]
    moodle.get_activities.return_value = []
    moodle.get_grades.return_value = []
    moodle.get_events.return_value = []
    repo = AsyncMock()
    repo.save_cursos.return_value = 1
    repo.save_actividades.return_value = 0
    repo.save_calificaciones.return_value = 0
    repo.save_interacciones.return_value = 0
    return SincronizarMoodleUseCase(moodle, repo, MagicMock())


@pytest.mark.asyncio
async def test_retorna_conteo(use_case):
    r = await use_case.execute(SincronizarMoodleCommand())
    assert r["registros_procesados"] == 1
    assert r["cursos"] == 1


@pytest.mark.asyncio
async def test_llama_api_por_curso(use_case):
    await use_case.execute(SincronizarMoodleCommand())
    use_case._moodle.get_activities.assert_called_once_with("c1")


@pytest.mark.asyncio
async def test_publica_evento(use_case):
    await use_case.execute(SincronizarMoodleCommand())
    use_case._event_publisher.publish.assert_called_once()
