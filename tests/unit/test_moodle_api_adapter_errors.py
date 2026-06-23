import httpx
import pytest

from src.domain.errors import LmsNoDisponibleError
from src.infrastructure.adapters.out_.moodle_api_adapter import MoodleApiAdapter


@pytest.mark.asyncio
async def test_call_traduce_error_httpx_a_error_de_dominio(monkeypatch):
    """Un fallo de transporte de httpx no debe filtrarse crudo al núcleo."""

    class _ClientQueFalla:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, *args, **kwargs):
            raise httpx.ConnectError("conexión rechazada")

    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _ClientQueFalla())

    adapter = MoodleApiAdapter()
    with pytest.raises(LmsNoDisponibleError):
        await adapter.get_courses()


@pytest.mark.asyncio
async def test_buscar_por_correo_traduce_error_httpx(monkeypatch):
    class _ClientQueFalla:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, *args, **kwargs):
            raise httpx.ConnectTimeout("timeout")

    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _ClientQueFalla())

    adapter = MoodleApiAdapter()
    with pytest.raises(LmsNoDisponibleError):
        await adapter.buscar_por_correo("x@sward.edu")
