"""Errores de dominio del microservicio de integración LMS.

El núcleo (domain/application) sólo conoce estos errores. Los adaptadores de
salida capturan los errores de su tecnología (httpx, etc.) y los re-lanzan
como uno de estos; un único exception handler en el borde HTTP los traduce a
códigos de respuesta. Así el núcleo nunca depende de FastAPI ni de httpx.
"""


class DomainError(Exception):
    """Error base del dominio de integración LMS."""


class LmsNoDisponibleError(DomainError):
    """El LMS (Moodle) no respondió o devolvió un error de transporte/HTTP.

    Encapsula fallos de la tecnología subyacente (timeouts, 5xx, errores de
    conexión) sin filtrar el detalle de httpx al núcleo.
    """


class UsuarioMoodleNoEncontradoError(DomainError):
    """No existe en Moodle un usuario con el correo solicitado."""

    def __init__(self, correo: str):
        self.correo = correo
        super().__init__(f"Correo no registrado en la plataforma educativa: {correo}")
