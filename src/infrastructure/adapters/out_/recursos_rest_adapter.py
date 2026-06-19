import logging

import httpx

from src.domain.entities.actividad_lms import ActividadLMS
from src.domain.ports.out_.recursos_client_port import RecursosClientPort
from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


class RecursosRestAdapter(RecursosClientPort):
    """Envía las actividades de Moodle a ms-cursos-recursos vía s2s (X-Service-Key)."""

    async def sync_recursos(self, actividades: list[ActividadLMS]) -> None:
        if settings.environment == "development" or not actividades:
            return
        payload = [
            {
                "moodle_activity_id": str(a.moodle_activity_id),
                "moodle_course_id": str(a.moodle_course_id),
                "titulo": a.nombre,
                "tipo": a.tipo or "",
            }
            for a in actividades
        ]
        headers = (
            {"X-Service-Key": settings.service_key} if settings.service_key else {}
        )
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(
                    f"{settings.cursos_service_url}/internal/resources/sync",
                    json={"recursos": payload},
                    headers=headers,
                )
                if r.status_code != 200:
                    logger.warning(
                        "sync recursos respondio %s: %s", r.status_code, r.text[:200]
                    )
                else:
                    logger.info(
                        "sync recursos enviado a cursos-recursos: %d", len(actividades)
                    )
        except Exception as exc:
            logger.error("Error al sincronizar recursos con cursos-recursos: %s", exc)
