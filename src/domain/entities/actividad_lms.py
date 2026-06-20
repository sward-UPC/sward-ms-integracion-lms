from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class ActividadLMS:
    id: UUID = field(default_factory=uuid4)
    moodle_activity_id: str = ""
    moodle_course_id: str = ""
    nombre: str = ""
    tipo: str = ""
    url: str = ""
    seccion: str = ""
