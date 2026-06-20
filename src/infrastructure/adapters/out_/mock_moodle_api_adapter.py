from src.domain.entities.actividad_lms import ActividadLMS
from src.domain.entities.calificacion_lms import CalificacionLMS
from src.domain.entities.curso_lms import CursoLMS
from src.domain.entities.interaccion_lms import InteraccionLMS
from src.domain.ports.out_.moodle_api_port import MoodleApiPort

MOCK_USERS = {
    "estudiante01@sward.edu": {
        "moodle_user_id": 7,
        "nombre": "Estudiante",
        "apellido": "Uno",
        "rol": "estudiante",
    },
    "estudiante02@sward.edu": {
        "moodle_user_id": 8,
        "nombre": "Estudiante",
        "apellido": "Dos",
        "rol": "estudiante",
    },
    "docente01@sward.edu": {
        "moodle_user_id": 2,
        "nombre": "Docente",
        "apellido": "Uno",
        "rol": "docente",
    },
}

MOCK_COURSES = [
    {
        "id": "course-101",
        "nombre": "Algoritmos y Estructuras de Datos",
        "codigo": "CS101",
    },
    {"id": "course-102", "nombre": "Bases de Datos", "codigo": "CS102"},
    {"id": "course-103", "nombre": "Ingeniería de Software", "codigo": "CS103"},
]


class MockMoodleApiAdapter(MoodleApiPort):
    async def get_courses(self) -> list[CursoLMS]:
        return [
            CursoLMS(moodle_course_id=c["id"], nombre=c["nombre"], codigo=c["codigo"])
            for c in MOCK_COURSES
        ]

    async def get_activities(self, moodle_course_id: str) -> list[ActividadLMS]:
        return [
            ActividadLMS(
                moodle_activity_id=f"{moodle_course_id}-act-1",
                moodle_course_id=moodle_course_id,
                nombre="Quiz 1",
                tipo="quiz",
            ),
            ActividadLMS(
                moodle_activity_id=f"{moodle_course_id}-act-2",
                moodle_course_id=moodle_course_id,
                nombre="Tarea 1",
                tipo="assign",
            ),
        ]

    async def get_course_resources(self, moodle_course_id: str) -> list[dict]:
        return [
            {
                "seccion": "Semana 1-2: Fundamentos",
                "nombre": "Lectura: Introducción",
                "tipo": "page",
                "url": f"https://moodle.example/mod/page/view.php?id={moodle_course_id}-1",
            },
        ]

    async def get_grades(self, moodle_course_id: str) -> list[CalificacionLMS]:
        return [
            CalificacionLMS(
                moodle_user_id="user-1",
                moodle_activity_id=f"{moodle_course_id}-act-1",
                moodle_course_id=moodle_course_id,
                puntaje=85.0,
            ),
            CalificacionLMS(
                moodle_user_id="user-2",
                moodle_activity_id=f"{moodle_course_id}-act-1",
                moodle_course_id=moodle_course_id,
                puntaje=72.0,
            ),
        ]

    async def buscar_por_correo(self, correo: str) -> dict | None:
        entry = MOCK_USERS.get(correo.lower())
        if not entry:
            return None
        return {**entry, "correo": correo}

    async def get_events(self, moodle_course_id: str) -> list[InteraccionLMS]:
        return [
            InteraccionLMS(
                moodle_user_id="user-1",
                moodle_course_id=moodle_course_id,
                moodle_activity_id=f"{moodle_course_id}-act-1",
                concepto="Unidad 1 - Fundamentos",
                accion="submitted",
                es_correcta=True,
            ),
            InteraccionLMS(
                moodle_user_id="user-2",
                moodle_course_id=moodle_course_id,
                moodle_activity_id=f"{moodle_course_id}-act-1",
                concepto="Unidad 1 - Fundamentos",
                accion="viewed",
            ),
        ]
