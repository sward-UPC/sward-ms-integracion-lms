from src.domain.entities.actividad_lms import ActividadLMS
from src.domain.ports.out_.lms_repository_port import LmsRepositoryPort


class ConsultarActividadesLmsUseCase:
    def __init__(self, repo: LmsRepositoryPort):
        self._repo = repo

    async def execute(self, moodle_course_id: str | None = None) -> list[ActividadLMS]:
        return await self._repo.find_actividades(moodle_course_id)
