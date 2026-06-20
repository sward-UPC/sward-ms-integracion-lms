import logging

import httpx

from src.domain.entities.interaccion_lms import InteraccionLMS
from src.domain.ports.out_.trazabilidad_client_port import TrazabilidadClientPort
from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


class TrazabilidadRestAdapter(TrazabilidadClientPort):
    async def sync_interacciones(self, interacciones: list[InteraccionLMS]) -> None:
        if settings.environment == "development" or not interacciones:
            return
        payload = [
            {
                "moodle_user_id": i.moodle_user_id,
                "moodle_course_id": i.moodle_course_id,
                "moodle_activity_id": i.moodle_activity_id,
                "nombre": i.nombre,
                "correo": i.correo,
                "concepto": i.concepto,
                "es_correcta": bool(i.es_correcta),
                "nota": float(i.nota),
                "url_modulo": i.url_modulo,
                "tipo_recurso": i.tipo_recurso,
                "nombre_actividad": i.nombre_actividad,
                "es_vista": i.es_vista,
                "fecha_evento": i.fecha_evento.isoformat(),
                "moodle_event_id": i.moodle_event_id or "",
            }
            for i in interacciones
        ]
        headers = (
            {"X-Service-Key": settings.service_key} if settings.service_key else {}
        )
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(
                    f"{settings.trazabilidad_service_url}/internal/lms-sync",
                    json={"interacciones": payload},
                    headers=headers,
                )
                if r.status_code not in (200, 202):
                    logger.warning(
                        "lms-sync trazabilidad respondio %s: %s",
                        r.status_code,
                        r.text[:200],
                    )
                else:
                    logger.info(
                        "lms-sync enviado a trazabilidad: %d interacciones",
                        len(interacciones),
                    )
        except Exception as exc:
            logger.error("Error al sincronizar con trazabilidad: %s", exc)
