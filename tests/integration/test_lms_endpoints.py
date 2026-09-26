"""Tests de integración de los endpoints de integración LMS (in-process)."""

import pytest

SYNC = "/lms/sync"
COURSES = "/lms/courses"
ACTIVITIES = "/lms/activities"
LOOKUP = "/lms/users/lookup"
HEALTH = "/health"


@pytest.mark.asyncio
async def test_health_ok(client):
    resp = await client.get(HEALTH)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_endpoint_protegido_sin_token_retorna_401(anon_client):
    resp = await anon_client.get(COURSES)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_courses_vacio_antes_de_sincronizar(client):
    resp = await client.get(COURSES)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_sync_procesa_datos_del_mock_moodle(client):
    resp = await client.post(SYNC)
    assert resp.status_code == 202
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


@pytest.mark.asyncio
async def test_lookup_usuario_existente(client):
    resp = await client.get(LOOKUP, params={"correo": "docente01@sward.edu"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["moodle_user_id"] == 2
    assert body["rol"] == "docente"


@pytest.mark.asyncio
async def test_lookup_usuario_inexistente_retorna_404(client):
    resp = await client.get(LOOKUP, params={"correo": "nadie@sward.edu"})
    assert resp.status_code == 404


# ------------------------------------------------------- alta de participantes
# El alta la hacía un script externo alimentado por un formulario de Google.
# Desde el 24-sep-2026 es un endpoint que llama el registro de SWARD.

PROVISION = "/lms/users/provision"


@pytest.mark.asyncio
async def test_provisionar_da_de_alta_y_devuelve_el_usuario(client):
    resp = await client.post(
        PROVISION,
        json={
            "correo": "nuevo.participante@upc.edu.pe",
            "nombres": "Nuevo",
            "apellidos": "Participante",
        },
    )
    assert resp.status_code == 201
    cuerpo = resp.json()
    assert cuerpo["correo"] == "nuevo.participante@upc.edu.pe"
    assert cuerpo["rol"] == "estudiante"
    assert cuerpo["moodle_user_id"] > 0

    # Y a partir de aquí el lookup lo encuentra: es el mismo flujo que sigue
    # ms-usuarios para asignarle su rol.
    lookup = await client.get(LOOKUP, params={"correo": "nuevo.participante@upc.edu.pe"})
    assert lookup.status_code == 200
    assert lookup.json()["moodle_user_id"] == cuerpo["moodle_user_id"]


@pytest.mark.asyncio
async def test_provisionar_es_idempotente(client):
    datos = {"correo": "repetido@upc.edu.pe", "nombres": "Ana", "apellidos": "Torres"}
    primero = await client.post(PROVISION, json=datos)
    segundo = await client.post(PROVISION, json=datos)
    assert primero.status_code == segundo.status_code == 201
    assert primero.json()["moodle_user_id"] == segundo.json()["moodle_user_id"]


@pytest.mark.asyncio
async def test_provisionar_rechaza_datos_incompletos(client):
    resp = await client.post(PROVISION, json={"correo": "sin.nombre@upc.edu.pe"})
    assert resp.status_code == 422


# El endpoint queda detrás de la clave de servicio por construcción: está
# registrado en `internal_router`, que declara `Depends(require_service_key)`
# para todas sus rutas. No se prueba aquí porque en desarrollo no hay claves
# configuradas y el guardia deja pasar: la prueba mediría la configuración del
# entorno, no el código.
