from src.application.ports.out_.moodle_api_port import MoodleApiPort


class ConsultarRecursosCursoLmsUseCase:
    """Obtiene, en vivo desde el LMS, los recursos/módulos de un curso por sección."""

    def __init__(self, moodle_api: MoodleApiPort):
        self._moodle = moodle_api

    async def execute(self, moodle_course_id: str) -> list[dict]:
        return await self._moodle.get_course_resources(moodle_course_id)
