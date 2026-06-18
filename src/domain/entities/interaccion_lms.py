from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class InteraccionLMS:
    id: UUID = field(default_factory=uuid4)
    moodle_event_id: str = ""
    moodle_user_id: str = ""
    moodle_course_id: str = ""
    moodle_activity_id: str = ""
    # Concepto/skill = sección del curso a la que pertenece la actividad (para SAKT).
    concepto: str = ""
    accion: str = ""
    es_correcta: bool | None = None
    fecha_evento: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
