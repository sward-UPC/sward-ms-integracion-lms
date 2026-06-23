"""Contratos Pydantic (Response) del adaptador de entrada HTTP.

Organizados por concern (lms, usuarios, sync) en vez de un único archivo, según
buenas prácticas de organización. Se re-exportan aquí para que las rutas importen
desde `...adapters.in_.schemas` sin conocer el submódulo.
"""

from .lms import (
    ActividadLMSResponse,
    CalificacionLMSResponse,
    CursoLMSResponse,
    InteraccionLMSResponse,
    RecursoCursoResponse,
)
from .sync import SyncResultResponse
from .usuarios import UsuarioMoodleResponse

__all__ = [
    "CursoLMSResponse",
    "ActividadLMSResponse",
    "CalificacionLMSResponse",
    "InteraccionLMSResponse",
    "RecursoCursoResponse",
    "SyncResultResponse",
    "UsuarioMoodleResponse",
]
