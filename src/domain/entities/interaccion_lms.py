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
    # Datos del estudiante en Moodle (para mostrarlos en el dashboard sin depender
    # de que se haya registrado en SWARD).
    nombre: str = ""
    correo: str = ""
    # Concepto/skill = sección del curso a la que pertenece la actividad (para SAKT).
    concepto: str = ""
    accion: str = ""
    es_correcta: bool | None = None
    # Nota numérica 0-100 (graderaw/grademax). Para el dominio continuo por sección.
    nota: float = 0.0
    # Enlace directo al módulo en Moodle (para abrirlo desde el panel docente).
    url_modulo: str = ""
    # Nombre real de la actividad en Moodle (p.ej. "Práctica 5: Normalización").
    nombre_actividad: str = ""
    fecha_evento: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
