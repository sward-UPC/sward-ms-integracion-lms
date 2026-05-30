"""Tests de integración de los endpoints de integración LMS (in-process)."""

import pytest

SYNC = "/lms/sync"
COURSES = "/lms/courses"
ACTIVITIES = "/lms/activities"
HEALTH = "/health"


@pytest.mark.asyncio
async def test_health_ok(client):
    resp = await client.get(HEALTH)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_courses_vacio_antes_de_sincronizar(client):
    resp = await client.get(COURSES)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_sync_procesa_datos_del_mock_moodle(client):
    resp = await client.post(SYNC)
    assert resp.status_code == 200
    body = resp.json()
    # El mock entrega 3 cursos y registros asociados.
    assert body["cursos"] == 3
    assert body["registros_procesados"] > 3


@pytest.mark.asyncio
async def test_flujo_sync_luego_courses_devuelve_lo_sincronizado(client):
    await client.post(SYNC)

    resp = await client.get(COURSES)
    assert resp.status_code == 200
    cursos = resp.json()
    assert len(cursos) == 3
    codigos = {c["codigo"] for c in cursos}
    assert {"CS101", "CS102", "CS103"} == codigos
    assert all(c["moodle_course_id"] for c in cursos)


@pytest.mark.asyncio
async def test_sync_persiste_actividades(client):
    await client.post(SYNC)

    resp = await client.get(ACTIVITIES)
    assert resp.status_code == 200
    # 3 cursos x 2 actividades cada uno.
    assert len(resp.json()) == 6
