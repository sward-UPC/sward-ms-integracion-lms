from src.domain.entities.actividad_lms import ActividadLMS
from src.domain.entities.calificacion_lms import CalificacionLMS
from src.domain.entities.curso_lms import CursoLMS
from src.domain.entities.interaccion_lms import InteraccionLMS
from src.application.ports.out_.moodle_api_port import MoodleApiPort

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

# Los dos cursos de la validación del OE4. Van aparte de MOCK_COURSES porque esa
# lista es fixture de las pruebas de sincronización, que cuentan sus elementos:
# agregarlos ahí cambiaba los totales y rompía tres pruebas ajenas.
CURSOS_DE_VALIDACION = [
    {"id": "course-201", "nombre": "Estadística", "codigo": "SWARD-EST"},
    {"id": "course-202", "nombre": "Matemática Financiera", "codigo": "SWARD-MF"},
]

# Matrículas hechas por el mock, para que las pruebas puedan comprobarlas.
MOCK_MATRICULAS: list[dict] = []


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
                url=f"https://moodle.example/mod/quiz/view.php?id={moodle_course_id}-1",
                seccion="Semana 1-2: Fundamentos",
            ),
            ActividadLMS(
                moodle_activity_id=f"{moodle_course_id}-act-2",
                moodle_course_id=moodle_course_id,
                nombre="Tarea 1",
                tipo="assign",
                url=f"https://moodle.example/mod/assign/view.php?id={moodle_course_id}-2",
                seccion="Semana 3-4: Estructuras",
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

    # ------------------------------------------------------------------ escritura
    # El mock sí crea y matricula de verdad sobre sus diccionarios: así una prueba
    # puede registrar a alguien y luego encontrarlo, que es el flujo que importa.
    async def crear_usuario(self, correo: str, nombres: str, apellidos: str) -> dict:
        nuevo_id = (
            max((u["moodle_user_id"] for u in MOCK_USERS.values()), default=100) + 1
        )
        username = correo.split("@")[0].lower()
        MOCK_USERS[correo.lower()] = {
            "moodle_user_id": nuevo_id,
            "nombre": nombres,
            "apellido": apellidos,
            "rol": "estudiante",
        }
        return {"moodle_user_id": nuevo_id, "username": username}

    async def buscar_curso_por_codigo(self, codigo: str) -> dict | None:
        for c in MOCK_COURSES + CURSOS_DE_VALIDACION:
            if c["codigo"].lower() == codigo.lower():
                return {
                    "moodle_course_id": c["id"],
                    "nombre": c["nombre"],
                    "codigo": c["codigo"],
                }
        return None

    async def matricular(
        self, moodle_user_id: int, moodle_course_id: str, rol: str
    ) -> None:
        MOCK_MATRICULAS.append(
            {
                "moodle_user_id": moodle_user_id,
                "moodle_course_id": moodle_course_id,
                "rol": rol,
            }
        )

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

    async def get_resource_views(self, moodle_course_id: str) -> list[InteraccionLMS]:
        return []
