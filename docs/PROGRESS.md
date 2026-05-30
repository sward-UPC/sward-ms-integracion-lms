# PROGRESS — sward-ms-integracion-lms

## Sprint 2 — 2026-05-29

### Implementado
- [x] Entidades: CursoLMS, ActividadLMS, CalificacionLMS, InteraccionLMS
- [x] Evento: DatosLmsSincronizadosEvent
- [x] Use Cases: ConsultarCursos, ConsultarActividades, ConsultarCalificaciones, ConsultarInteracciones, SincronizarMoodle
- [x] MockMoodleApiAdapter con 3 cursos y datos realistas
- [x] MoodleApiAdapter real (cursos y actividades)
- [x] LmsPostgresAdapter con upsert por moodle_id
- [x] Endpoints: GET /lms/courses, /activities, /grades, /interactions, POST /lms/sync
- [x] Docker Compose: PostgreSQL 15
- [x] Tests unitarios: 3 tests (SincronizarMoodle)
