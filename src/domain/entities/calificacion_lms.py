from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class CalificacionLMS:
    id: UUID = field(default_factory=uuid4)
    moodle_user_id: str = ""
    moodle_activity_id: str = ""
    moodle_course_id: str = ""
    puntaje: float = 0.0
    puntaje_maximo: float = 100.0
    fecha: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
