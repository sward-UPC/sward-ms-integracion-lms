"""La identidad de una interacción debe distinguir actividades distintas.

Moodle numera las instancias por tipo de módulo: la tarea 1 y el cuestionario 1
son actividades distintas con la misma `iteminstance`. Si esa instancia se usa
como identidad, ambas producen el mismo `moodle_event_id`, el upsert de
trazabilidad conserva una sola fila y esa fila se queda con el curso y el
concepto de la última en escribirse: se pierden interacciones y las secuencias
del KT quedan mezcladas entre cursos.

El `cmid` (id del módulo dentro del curso) sí es único en todo Moodle.
"""

import pytest

from src.infrastructure.adapters.out_.moodle_api_adapter import MoodleApiAdapter


CONTENIDOS = [
    {
        "name": "Introducción a los Algoritmos",
        "modules": [
            {"id": 101, "modname": "assign", "instance": 1, "name": "Práctica 1", "url": "u1"},
            {"id": 102, "modname": "quiz", "instance": 1, "name": "Quiz 1", "url": "u2"},
        ],
    }
]

# Dos actividades distintas del mismo alumno que comparten `iteminstance`.
GRADE_ITEMS = {
    "usergrades": [
        {
            "gradeitems": [
                {
                    "itemtype": "mod",
                    "itemmodule": "assign",
                    "iteminstance": 1,
                    "itemname": "Práctica 1",
                    "graderaw": 18.0,
                    "grademax": 20.0,
                },
                {
                    "itemtype": "mod",
                    "itemmodule": "quiz",
                    "iteminstance": 1,
                    "itemname": "Quiz 1",
                    "graderaw": 12.0,
                    "grademax": 20.0,
                },
            ]
        }
    ]
}


def _adaptador_falso(monkeypatch):
    adapter = MoodleApiAdapter()

    async def _call(fn, **kw):
        if fn == "core_course_get_contents":
            return CONTENIDOS
        if fn == "core_enrol_get_enrolled_users":
            return [{"id": 5, "fullname": "Estudiante 05", "email": "e05@sward-test.com"}]
        if fn == "gradereport_user_get_grade_items":
            return GRADE_ITEMS
        return []

    monkeypatch.setattr(adapter, "_call", _call)
    return adapter


@pytest.mark.asyncio
async def test_dos_actividades_con_la_misma_instancia_no_comparten_identidad(monkeypatch):
    adapter = _adaptador_falso(monkeypatch)

    interacciones = await adapter.get_events("2")

    assert len(interacciones) == 2
    ids = {i.moodle_event_id for i in interacciones}
    assert len(ids) == 2, f"identidades colisionadas: {ids}"


@pytest.mark.asyncio
async def test_la_identidad_usa_el_cmid_no_la_instancia(monkeypatch):
    adapter = _adaptador_falso(monkeypatch)

    interacciones = await adapter.get_events("2")

    por_nombre = {i.nombre_actividad: i for i in interacciones}
    assert por_nombre["Práctica 1"].moodle_activity_id == "101"
    assert por_nombre["Quiz 1"].moodle_activity_id == "102"
    assert por_nombre["Práctica 1"].moodle_event_id == "5-101"
    assert por_nombre["Quiz 1"].moodle_event_id == "5-102"


@pytest.mark.asyncio
async def test_el_concepto_sigue_siendo_la_seccion_del_curso(monkeypatch):
    # El arreglo de la identidad no debe alterar el concepto que consume el SAKT.
    adapter = _adaptador_falso(monkeypatch)

    interacciones = await adapter.get_events("2")

    assert {i.concepto for i in interacciones} == {"Introducción a los Algoritmos"}
    assert {i.moodle_course_id for i in interacciones} == {"2"}
