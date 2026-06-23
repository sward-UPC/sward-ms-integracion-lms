from src.domain.entities.interaccion_lms import InteraccionLMS
from src.application.ports.out_.lms_repository_port import LmsRepositoryPort


class ConsultarInteraccionesLmsUseCase:
    def __init__(self, repo: LmsRepositoryPort):
        self._repo = repo

    async def execute(
        self, moodle_course_id: str | None = None, moodle_user_id: str | None = None
    ) -> list[InteraccionLMS]:
        return await self._repo.find_interacciones(moodle_course_id, moodle_user_id)
