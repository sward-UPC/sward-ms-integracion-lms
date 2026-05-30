from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sward_shared.auth import build_require_jwt, build_require_service_key

from src.application.use_cases.consultar_actividades_lms import (
    ConsultarActividadesLmsUseCase,
)
from src.application.use_cases.consultar_calificaciones_lms import (
    ConsultarCalificacionesLmsUseCase,
)
from src.application.use_cases.consultar_cursos_lms import ConsultarCursosLmsUseCase
from src.application.use_cases.consultar_interacciones_lms import (
    ConsultarInteraccionesLmsUseCase,
)
from src.application.use_cases.sincronizar_moodle import SincronizarMoodleUseCase
from src.infrastructure.adapters.out_.eventbridge_adapter import EventBridgeAdapter
from src.infrastructure.adapters.out_.lms_postgres_adapter import LmsPostgresAdapter
from src.infrastructure.adapters.out_.mock_moodle_api_adapter import (
    MockMoodleApiAdapter,
)
from src.infrastructure.adapters.out_.moodle_api_adapter import MoodleApiAdapter
from src.infrastructure.config.settings import settings
from src.infrastructure.db.database import get_session

# Dependencia de autenticación JWT reutilizable, compartida vía sward-shared.
require_jwt = build_require_jwt(settings.secret_key, algorithm=settings.jwt_algorithm)

# Validación entrante de service-key (modo dev permite sin claves configuradas).
require_service_key = build_require_service_key(settings.authorized_service_keys_set)


@lru_cache(maxsize=1)
def get_eventbridge_adapter() -> EventBridgeAdapter:
    return EventBridgeAdapter()


def get_moodle_adapter():
    return MockMoodleApiAdapter() if settings.moodle_mock else MoodleApiAdapter()


def get_consultar_cursos_uc(
    session: AsyncSession = Depends(get_session),
) -> ConsultarCursosLmsUseCase:
    return ConsultarCursosLmsUseCase(LmsPostgresAdapter(session))


def get_consultar_actividades_uc(
    session: AsyncSession = Depends(get_session),
) -> ConsultarActividadesLmsUseCase:
    return ConsultarActividadesLmsUseCase(LmsPostgresAdapter(session))


def get_consultar_calificaciones_uc(
    session: AsyncSession = Depends(get_session),
) -> ConsultarCalificacionesLmsUseCase:
    return ConsultarCalificacionesLmsUseCase(LmsPostgresAdapter(session))


def get_consultar_interacciones_uc(
    session: AsyncSession = Depends(get_session),
) -> ConsultarInteraccionesLmsUseCase:
    return ConsultarInteraccionesLmsUseCase(LmsPostgresAdapter(session))


def get_sincronizar_moodle_uc(
    session: AsyncSession = Depends(get_session),
    events: EventBridgeAdapter = Depends(get_eventbridge_adapter),
) -> SincronizarMoodleUseCase:
    return SincronizarMoodleUseCase(
        get_moodle_adapter(), LmsPostgresAdapter(session), events
    )
