"""Fixtures de integración para los endpoints de integración LMS (in-process).

La app se ejerce con httpx.AsyncClient + ASGITransport (sin servidor).
Se conserva el MockMoodleApiAdapter real (moodle_mock=True) y se sustituye
únicamente el repositorio Postgres por uno en memoria compartido entre los
casos de uso de sync y de consulta, vía dependency_overrides.
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.application.use_cases.consultar_actividades_lms import (
    ConsultarActividadesLmsUseCase,
)
from src.application.use_cases.consultar_calificaciones_lms import (
    ConsultarCalificacionesLmsUseCase,
)
from src.application.use_cases.consultar_cursos_lms import ConsultarCursosLmsUseCase
from src.application.use_cases.consultar_interacciones_lms import (
    ConsultarInteraccionesLmsUseCase,
)
from src.application.use_cases.sincronizar_moodle import SincronizarMoodleUseCase
from src.domain.entities.actividad_lms import ActividadLMS
from src.domain.entities.calificacion_lms import CalificacionLMS
from src.domain.entities.curso_lms import CursoLMS
from src.domain.entities.interaccion_lms import InteraccionLMS
from src.domain.ports.out_.lms_repository_port import LmsRepositoryPort
from src.domain.ports.out_.trazabilidad_client_port import TrazabilidadClientPort
from src.infrastructure.adapters.in_.main import app
from src.infrastructure.adapters.out_.mock_moodle_api_adapter import (
    MockMoodleApiAdapter,
)
from src.infrastructure.dependencies import (
    get_consultar_actividades_uc,
    get_consultar_calificaciones_uc,
    get_consultar_cursos_uc,
    get_consultar_interacciones_uc,
    get_sincronizar_moodle_uc,
    require_jwt,
)

FAKE_PAYLOAD = {
    "sub": "00000000-0000-0000-0000-000000000001",
    "rol": "docente",
    "permisos": ["leer"],
    "type": "access",
}


class FakeLmsRepo(LmsRepositoryPort):
    def __init__(self):
        self.cursos: list[CursoLMS] = []
        self.actividades: list[ActividadLMS] = []
        self.calificaciones: list[CalificacionLMS] = []
        self.interacciones: list[InteraccionLMS] = []

    async def save_cursos(self, cursos: list[CursoLMS]) -> int:
        existentes = {c.moodle_course_id for c in self.cursos}
        nuevos = [c for c in cursos if c.moodle_course_id not in existentes]
        self.cursos.extend(nuevos)
        return len(nuevos)

    async def find_cursos(self) -> list[CursoLMS]:
        return list(self.cursos)

    async def save_actividades(self, actividades: list[ActividadLMS]) -> int:
        self.actividades.extend(actividades)
        return len(actividades)

    async def find_actividades(self, moodle_course_id: str | None = None):
        if moodle_course_id:
            return [
                a for a in self.actividades if a.moodle_course_id == moodle_course_id
            ]
        return list(self.actividades)

    async def save_calificaciones(self, calificaciones: list[CalificacionLMS]) -> int:
        self.calificaciones.extend(calificaciones)
        return len(calificaciones)

    async def find_calificaciones(self, moodle_course_id=None, moodle_user_id=None):
        items = self.calificaciones
        if moodle_course_id:
            items = [c for c in items if c.moodle_course_id == moodle_course_id]
        if moodle_user_id:
            items = [c for c in items if c.moodle_user_id == moodle_user_id]
        return list(items)

    async def save_interacciones(self, interacciones: list[InteraccionLMS]) -> int:
        self.interacciones.extend(interacciones)
        return len(interacciones)

    async def find_interacciones(self, moodle_course_id=None, moodle_user_id=None):
        items = self.interacciones
        if moodle_course_id:
            items = [i for i in items if i.moodle_course_id == moodle_course_id]
        if moodle_user_id:
            items = [i for i in items if i.moodle_user_id == moodle_user_id]
        return list(items)


class _StubEventPublisher:
    def publish(self, event) -> None:  # noqa: ARG002
        return None


class _StubTrazabilidadClient(TrazabilidadClientPort):
    async def sync_interacciones(self, interacciones) -> None:  # noqa: ARG002
        return None


@pytest_asyncio.fixture
async def client():
    repo = FakeLmsRepo()
    moodle = MockMoodleApiAdapter()
    events = _StubEventPublisher()
    trazabilidad = _StubTrazabilidadClient()

    app.dependency_overrides[get_sincronizar_moodle_uc] = lambda: (
        SincronizarMoodleUseCase(moodle, repo, events, trazabilidad)
    )
    app.dependency_overrides[get_consultar_cursos_uc] = lambda: (
        ConsultarCursosLmsUseCase(repo)
    )
    app.dependency_overrides[get_consultar_actividades_uc] = lambda: (
        ConsultarActividadesLmsUseCase(repo)
    )
    app.dependency_overrides[get_consultar_calificaciones_uc] = lambda: (
        ConsultarCalificacionesLmsUseCase(repo)
    )
    app.dependency_overrides[get_consultar_interacciones_uc] = lambda: (
        ConsultarInteraccionesLmsUseCase(repo)
    )
    # Sobreescribe la validación JWT por un payload fake (autenticación simulada).
    app.dependency_overrides[require_jwt] = lambda: FAKE_PAYLOAD

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def anon_client():
    """Cliente sin override de auth: los endpoints protegidos exigen token real."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
