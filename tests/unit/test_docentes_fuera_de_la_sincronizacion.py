"""El docente del curso no es un estudiante más.

`core_enrol_get_enrolled_users` devuelve a TODOS los matriculados, docentes
incluidos, y de esa lista salen las notas, los recursos vistos y los eventos que
SWARD guarda como actividad de estudiante. Sin filtrar, la profesora del estudio
aparecía en su propio panel como una alumna con nivel de riesgo crítico, y
contaba en el promedio del curso y en el conteo de estudiantes en riesgo, que
son cifras del OE4.

Moodle sí trae el rol: en la nube devuelve `teacher` para la profesora y
`student` para los participantes.
"""

import pytest

from src.infrastructure.adapters.out_.moodle_api_adapter import MoodleApiAdapter

CONTENIDOS = [
    {
        "name": "Interés simple",
        "modules": [
            {
                "id": 101,
                "modname": "quiz",
                "instance": 1,
                "name": "Quiz 1",
                "url": "u1",
            }
        ],
    }
]

GRADE_ITEMS = {
    "usergrades": [
        {
            "gradeitems": [
                {
                    "itemtype": "mod",
                    "itemmodule": "quiz",
                    "iteminstance": 1,
                    "itemname": "Quiz 1",
                    "graderaw": 15.0,
                    "grademax": 20.0,
                }
            ]
        }
    ]
}

# Los mismos roles que devuelve el Moodle del estudio.
MATRICULADOS = [
    {
        "id": 19,
        "fullname": "Katherine Vasquez",
        "email": "docente@ejemplo.com",
        "roles": [{"shortname": "teacher"}],
    },
    {
        "id": 20,
        "fullname": "Participante 20",
        "email": "p20@ejemplo.com",
        "roles": [{"shortname": "student"}],
    },
]


def _adaptador(monkeypatch, matriculados):
    adapter = MoodleApiAdapter()

    async def _call(fn, **kw):
        if fn == "core_course_get_contents":
            return CONTENIDOS
        if fn == "core_enrol_get_enrolled_users":
            return matriculados
        if fn == "gradereport_user_get_grade_items":
            return GRADE_ITEMS
        return []

    monkeypatch.setattr(adapter, "_call", _call)
    return adapter


@pytest.mark.asyncio
async def test_las_notas_del_docente_no_se_sincronizan(monkeypatch):
    adapter = _adaptador(monkeypatch, MATRICULADOS)

    notas = await adapter.get_grades("3")

    assert [n.moodle_user_id for n in notas] == ["20"]


@pytest.mark.asyncio
async def test_los_eventos_del_docente_no_se_sincronizan(monkeypatch):
    adapter = _adaptador(monkeypatch, MATRICULADOS)

    eventos = await adapter.get_events("3")

    assert {e.moodle_user_id for e in eventos} == {"20"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "rol", ["editingteacher", "teacher", "manager", "coursecreator"]
)
async def test_ningun_rol_de_quien_dicta_pasa_el_filtro(monkeypatch, rol):
    solo_docente = [{**MATRICULADOS[0], "roles": [{"shortname": rol}]}]
    adapter = _adaptador(monkeypatch, solo_docente)

    assert await adapter.get_grades("3") == []


@pytest.mark.asyncio
async def test_sin_el_arreglo_de_roles_no_se_descarta_a_nadie(monkeypatch):
    # Si el token dejara de devolver los roles, la sincronización tiene que
    # seguir trayendo a los estudiantes en vez de apagarse en silencio.
    sin_roles = [{"id": 20, "fullname": "Participante 20", "email": "p20@ejemplo.com"}]
    adapter = _adaptador(monkeypatch, sin_roles)

    notas = await adapter.get_grades("3")

    assert [n.moodle_user_id for n in notas] == ["20"]
