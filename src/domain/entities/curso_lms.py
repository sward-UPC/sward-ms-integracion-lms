from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class CursoLMS:
    id: UUID = field(default_factory=uuid4)
    moodle_course_id: str = ""
    nombre: str = ""
    codigo: str = ""
    activo: bool = True
