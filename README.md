# sward-ms-integracion-lms

Microservicio de **integración con el LMS (Moodle)** del sistema **SWARD**.

Es el único punto de SWARD que habla con Moodle. Su responsabilidad es
**sincronizar e ingerir** los datos académicos de Moodle (cursos, actividades,
calificaciones e interacciones) y **exponer el catálogo LMS normalizado** al
resto de microservicios. Durante la sincronización propaga además esos datos a
otros servicios: las interacciones a **ms-trazabilidad** (alimenta el modelo
SAKT) y los cursos/actividades a **ms-cursos-recursos** (catálogo).

---

## Qué hace

- **Sincroniza Moodle** vía su Web Service REST: lee cursos, contenidos
  (actividades y lecturas), calificaciones por usuario, interacciones
  (entregas calificadas) y vistas de lecturas/recursos.
- **Persiste** el catálogo en PostgreSQL (upsert por `moodle_*_id`).
- **Expone** consultas de cursos, actividades, calificaciones e interacciones
  al resto de SWARD (endpoints protegidos por JWT).
- **Resuelve identidad**: busca usuarios de Moodle por correo y deduce su rol
  (estudiante / docente). Usado por **ms-usuarios** durante el registro.
- **Publica** el evento de dominio `DatosLmsSincronizados` en EventBridge y
  propaga interacciones/recursos a los servicios consumidores.
- En desarrollo usa un **adaptador mock** de Moodle (`MOODLE_MOCK=true`) con
  datos realistas, intercambiable por el adaptador real sin tocar el núcleo.

---

## Stack

- **Python 3.11** · **FastAPI** · **Uvicorn**
- **SQLAlchemy 2.0 (async)** · **asyncpg** · **PostgreSQL 15**
- **Pydantic v2** / **pydantic-settings** (configuración)
- **httpx** (cliente HTTP async hacia Moodle y servicios s2s)
- **boto3** (EventBridge, en producción)
- **scalar-fastapi** (referencia de API interactiva)
- **sward-shared** (auth JWT/service-key, eventos de dominio, adaptador
  EventBridge — librería compartida del monorepo de la org)
- Calidad: **pytest** · **pytest-asyncio** · **ruff** · **bandit** · **pip-audit**

---

## Arquitectura hexagonal (Ports & Adapters)

El núcleo (`domain`, `application`) no conoce FastAPI, SQLAlchemy, httpx ni
boto3. Esos detalles viven solo en `infrastructure`. Los adaptadores de entrada
están en `adapters/in_` y los de salida en `adapters/out_`.

```
src/
├── domain/                                  # NÚCLEO: sin dependencias de frameworks
│   ├── entities/
│   │   ├── curso_lms.py                      # CursoLMS
│   │   ├── actividad_lms.py                  # ActividadLMS
│   │   ├── calificacion_lms.py              # CalificacionLMS
│   │   └── interaccion_lms.py               # InteraccionLMS
│   ├── events/
│   │   └── datos_lms_sincronizados_event.py # DatosLmsSincronizadosEvent
│   └── ports/out_/                           # contratos que el núcleo necesita
│       ├── moodle_api_port.py                # MoodleApiPort
│       ├── lms_repository_port.py            # LmsRepositoryPort
│       ├── event_publisher_port.py           # EventPublisherPort
│       ├── cursos_client_port.py             # CursosClientPort
│       ├── recursos_client_port.py           # RecursosClientPort
│       └── trazabilidad_client_port.py       # TrazabilidadClientPort
│
├── application/use_cases/                    # casos de uso (orquestación)
│   ├── sincronizar_moodle.py                 # SincronizarMoodleUseCase
│   ├── consultar_cursos_lms.py
│   ├── consultar_actividades_lms.py
│   ├── consultar_calificaciones_lms.py
│   └── consultar_interacciones_lms.py
│
└── infrastructure/
    ├── adapters/
    │   ├── in_/                               # adaptadores de ENTRADA
    │   │   ├── main.py                        # app FastAPI, CORS, handlers, lifespan
    │   │   └── lms_router.py                  # routers público (JWT) e interno (service-key)
    │   └── out_/                              # adaptadores de SALIDA (implementan ports/)
    │       ├── moodle_api_adapter.py          # cliente real de la WS REST de Moodle
    │       ├── mock_moodle_api_adapter.py     # mock para desarrollo
    │       ├── lms_postgres_adapter.py        # persistencia SQLAlchemy
    │       ├── eventbridge_adapter.py         # publica eventos de dominio
    │       ├── cursos_rest_adapter.py         # s2s → ms-cursos-recursos (cursos)
    │       ├── recursos_rest_adapter.py       # s2s → ms-cursos-recursos (recursos)
    │       └── trazabilidad_rest_adapter.py   # s2s → ms-trazabilidad (interacciones)
    ├── config/
    │   └── settings.py                        # configuración (pydantic-settings)
    ├── db/
    │   ├── database.py                        # engine + sesión async
    │   └── models/lms_models.py               # modelos ORM
    └── dependencies.py                        # composition root (wiring de Depends)
```

El único lugar que conoce implementaciones concretas es
`infrastructure/dependencies.py`: ahí se eligen mock/real de Moodle y se
inyectan los puertos a los casos de uso.

---

## Endpoints

Base path: `/lms`. Documentación interactiva en `/scalar`; esquema OpenAPI en
`/lms/openapi.json`.

### Públicos (requieren **JWT** emitido por ms-usuarios)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/lms/courses` | Cursos sincronizados |
| GET | `/lms/activities?courseId=` | Actividades (filtro opcional por curso) |
| GET | `/lms/courses/{moodle_course_id}/resources` | Recursos/módulos por sección, en vivo desde Moodle |
| GET | `/lms/grades?courseId=&userId=` | Calificaciones (filtros opcionales) |
| GET | `/lms/interactions?courseId=&userId=` | Interacciones (filtros opcionales) |

### Internos (requieren **X-Service-Key**, los llaman lambdas/servicios)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/lms/users/lookup?correo=` | Busca usuario en Moodle por correo y deduce rol (lo usa ms-usuarios en el registro) |
| POST | `/lms/sync` | Dispara la sincronización completa desde Moodle (ingesta + propagación) |

### Operación

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Sonda de estado (incluye si opera en modo mock) |
| GET | `/scalar` | Referencia de API interactiva (Scalar) |

> **`POST /lms/sync`** es el endpoint interno central del servicio: ejecuta
> `SincronizarMoodleUseCase`, que lee Moodle, hace upsert en PostgreSQL,
> publica `DatosLmsSincronizados` en EventBridge y propaga interacciones a
> ms-trazabilidad y cursos/recursos a ms-cursos-recursos. En desarrollo las
> propagaciones s2s y la publicación a EventBridge se omiten (solo log).

---

## Variables de entorno

Ver `.env.example`. Resumen:

| Variable | Descripción | Default |
|---|---|---|
| `ENVIRONMENT` | `development` activa mock de Moodle por defecto y desactiva s2s/EventBridge reales | `development` |
| `DATABASE_URL` | DSN async de PostgreSQL | `postgresql+asyncpg://sward:sward@localhost:5432/integracion_lms_db` |
| `DB_USERNAME` / `DB_PASSWORD` / `DATABASE_HOST` / `DATABASE_PORT` / `DATABASE_NAME` | Componentes inyectados por ECS (Secrets Manager); si están presentes, recomponen `DATABASE_URL` | `""` / `5432` |
| **`MOODLE_BASE_URL`** | URL base de la instancia Moodle | `https://moodle.example.com` |
| **`MOODLE_TOKEN`** | Token del Web Service REST de Moodle (`wstoken`) | `mock-token` |
| **`MOODLE_MOCK`** | `true` usa `MockMoodleApiAdapter` (sin Moodle real) | `true` |
| `AWS_REGION` | Región AWS para EventBridge | `us-east-1` |
| `EVENTBRIDGE_BUS_NAME` | Nombre del event bus de EventBridge | `sward-event-bus` |
| `SECRET_KEY` | Secreto HS256 para validar el JWT (emitido por ms-usuarios). Obligatorio cambiarlo fuera de `development` | `dev-secret-change-in-production` |
| `JWT_ALGORITHM` | Algoritmo del JWT | `HS256` |
| `SERVICE_KEY` | Clave que este servicio envía como `X-Service-Key` en llamadas salientes s2s | `""` |
| `AUTHORIZED_SERVICE_KEYS` | Claves entrantes autorizadas, separadas por coma (modo manual/legacy) | `""` |
| `AUTHORIZED_TRAZABILIDAD_KEY` / `AUTHORIZED_USUARIOS_KEY` | Claves entrantes por caller, inyectadas por CDK (Secrets Manager) | `""` |
| `TRAZABILIDAD_SERVICE_URL` | URL de ms-trazabilidad (Cloud Map DNS en ECS) | `http://trazabilidad.sward.local:8000` |
| `CURSOS_SERVICE_URL` | URL de ms-cursos-recursos (Cloud Map DNS en ECS) | `http://cursos-recursos.sward.local:8000` |
| `CORS_ALLOWED_ORIGINS` | Orígenes permitidos para CORS | `["http://localhost:5173"]` |

---

## Cómo correr

### Local (con PostgreSQL en Docker)

```bash
cp .env.example .env

# Levanta solo la base de datos (PostgreSQL 15, puerto host 5434)
docker compose up -d db

# Instala dependencias (entorno virtual)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Arranca el servicio (crea las tablas al iniciar, vía lifespan)
uvicorn src.infrastructure.adapters.in_.main:app --reload --port 8002
```

Con `MOODLE_MOCK=true` no necesitas un Moodle real: el `MockMoodleApiAdapter`
sirve datos de ejemplo. La API queda en `http://localhost:8002`
(docs en `/scalar`).

### Todo en Docker Compose

```bash
docker compose up --build          # app en http://localhost:8002, db en :5434
```

---

## Tests y calidad

```bash
pytest -q                          # unitarios + integración
ruff check src tests               # linting
bandit -r src                      # análisis de seguridad estático
pip-audit                          # vulnerabilidades en dependencias
```

Los tests unitarios usan **fakes en memoria** que cumplen los puertos (sin BD ni
Moodle real); los de integración levantan la app FastAPI con `httpx`. Suite
actual: 12 tests en verde.

---

## Flujo de deploy

CI/CD vía workflows reutilizables de la organización `sward-UPC`:

- **CI** (`.github/workflows/ci.yml`): en `push`/`pull_request` a `main`
  ejecuta el workflow `ci-microservice.yml` (tests + lint), con
  `needs_shared: true` para resolver `sward-shared`.
- **Build & Push** (`.github/workflows/build-push.yml`): en `push` a la rama
  `deploy` construye la imagen Docker, la publica en **GHCR** y actualiza el
  servicio ECS (`build-push-ghcr.yml`):
  - `image_name: sward-ms-integracion-lms`
  - `aws_service_name: integracion-lms`
  - `aws_cluster_name: sward-cluster`

Resumen operativo: el servicio corre como contenedor en **ECS** (imagen en
GHCR), con PostgreSQL (RDS), descubrimiento de servicios por **Cloud Map**, y
secretos (DB, claves de servicio, `SECRET_KEY`, token de Moodle) inyectados por
**Secrets Manager** desde el stack de CDK. Para desplegar: fusionar a la rama
`deploy`.

---

## Proyecto

**TP202610051** — Universidad Peruana de Ciencias Aplicadas (UPC)
Taller de Proyecto · 2026
