from dataclasses import dataclass, field
from uuid import UUID, uuid4
from sward_shared.events.domain_event import DomainEvent


@dataclass
class DatosLmsSincronizadosEvent(DomainEvent):
    sincronizacion_id: UUID = field(default_factory=uuid4)
    registros_procesados: int = 0
    source: str = "sward-ms-integracion-lms"

    @property
    def event_type(self) -> str:
        return "sward.lms.DatosLmsSincronizados"
