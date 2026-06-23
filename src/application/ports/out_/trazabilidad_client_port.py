from abc import ABC, abstractmethod
from src.domain.entities.interaccion_lms import InteraccionLMS


class TrazabilidadClientPort(ABC):
    @abstractmethod
    async def sync_interacciones(self, interacciones: list[InteraccionLMS]) -> None: ...
