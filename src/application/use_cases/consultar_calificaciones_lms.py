from src.domain.entities.calificacion_lms import CalificacionLMS
from src.application.ports.out_.lms_repository_port import LmsRepositoryPort


class ConsultarCalificacionesLmsUseCase:
    def __init__(self, repo: LmsRepositoryPort):
        self._repo = repo

    async def execute(
        self, moodle_course_id: str | None = None, moodle_user_id: str | None = None
    ) -> list[CalificacionLMS]:
        return await self._repo.find_calificaciones(moodle_course_id, moodle_user_id)
