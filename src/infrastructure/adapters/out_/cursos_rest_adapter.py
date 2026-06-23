import logging

import httpx

from src.domain.entities.curso_lms import CursoLMS
from src.application.ports.out_.cursos_client_port import CursosClientPort
from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


class CursosRestAdapter(CursosClientPort):
    """Envía los cursos sincronizados a ms-cursos-recursos vía s2s (X-Service-Key)."""

    async def sync_cursos(self, cursos: list[CursoLMS]) -> None:
        if settings.environment == "development" or not cursos:
            return
        payload = [
            {
                "moodle_course_id": str(c.moodle_course_id),
                "nombre": c.nombre,
                "codigo": c.codigo or "",
            }
            for c in cursos
        ]
        headers = (
            {"X-Service-Key": settings.service_key} if settings.service_key else {}
        )
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(
                    f"{settings.cursos_service_url}/internal/courses/sync",
                    json={"cursos": payload},
                    headers=headers,
                )
                if r.status_code != 200:
                    logger.warning(
                        "sync cursos respondio %s: %s", r.status_code, r.text[:200]
                    )
                else:
                    logger.info(
                        "sync cursos enviado a cursos-recursos: %d", len(cursos)
                    )
        except Exception as exc:
            logger.error("Error al sincronizar cursos con cursos-recursos: %s", exc)
