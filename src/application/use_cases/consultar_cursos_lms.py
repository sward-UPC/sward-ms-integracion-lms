from src.domain.entities.curso_lms import CursoLMS
from src.domain.ports.out_.lms_repository_port import LmsRepositoryPort


class ConsultarCursosLmsUseCase:
    def __init__(self, repo: LmsRepositoryPort):
        self._repo = repo

    async def execute(self) -> list[CursoLMS]:
        return await self._repo.find_cursos()
