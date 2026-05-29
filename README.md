# sward-ms-integracion-lms

Microservicio de integración con **Moodle LMS** del sistema **SWARD**.  
Expone datos académicos sincronizados desde Moodle a los demás microservicios del sistema.

## Arquitectura

Arquitectura **Hexagonal (Ports & Adapters)**:

```
src/
  domain/           # CursoLMS, ActividadLMS, CalificacionLMS, InteraccionLMS
  application/      # ConsultarCursosLmsUseCase, SincronizarMoodleUseCase...
  infrastructure/   # FastAPI routers, PostgresAdapter, MoodleApiAdapter (+ Mock)
```

## Stack

- Python 3.11 · FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL
- httpx (cliente HTTP) · Pydantic v2 · boto3

## Desarrollo local

```bash
cp .env.example .env
docker compose up -d db
alembic upgrade head
uvicorn src.infrastructure.adapters.in_.main:app --reload --port 8002
```

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/lms/courses` | Cursos sincronizados |
| GET | `/lms/activities` | Actividades por curso |
| GET | `/lms/grades` | Calificaciones |
| GET | `/lms/interactions` | Interacciones académicas |
| POST | `/lms/sync` | Disparar sincronización manual |

> Para desarrollo se usa `MockMoodleApiAdapter` cuando `MOODLE_MOCK=true`.

## Proyecto

**TP202610051** — Universidad Peruana de Ciencias Aplicadas (UPC)  
Taller de Proyecto 1 / 2026
