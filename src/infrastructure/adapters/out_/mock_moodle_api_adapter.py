from src.domain.entities.actividad_lms import ActividadLMS
from src.domain.entities.calificacion_lms import CalificacionLMS
from src.domain.entities.curso_lms import CursoLMS
from src.domain.entities.interaccion_lms import InteraccionLMS
from src.domain.ports.out_.moodle_api_port import MoodleApiPort

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

    async def get_events(self, moodle_course_id: str) -> list[InteraccionLMS]:
        return [
            InteraccionLMS(
                moodle_user_id="user-1",
                moodle_course_id=moodle_course_id,
                moodle_activity_id=f"{moodle_course_id}-act-1",
                accion="submitted",
                es_correcta=True,
            ),
            InteraccionLMS(
                moodle_user_id="user-2",
                moodle_course_id=moodle_course_id,
                moodle_activity_id=f"{moodle_course_id}-act-1",
                accion="viewed",
            ),
        ]
