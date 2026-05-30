from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CursoLmsModel(Base):
    __tablename__ = "lms_courses"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    moodle_course_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class ActividadLmsModel(Base):
    __tablename__ = "lms_activities"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    moodle_activity_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    moodle_course_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), default="")


class CalificacionLmsModel(Base):
    __tablename__ = "lms_grades"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    moodle_user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    moodle_activity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    moodle_course_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    puntaje: Mapped[float] = mapped_column(Float, default=0.0)
    puntaje_maximo: Mapped[float] = mapped_column(Float, default=100.0)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class InteraccionLmsModel(Base):
    __tablename__ = "lms_interactions"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    moodle_event_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    moodle_user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    moodle_course_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    moodle_activity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    accion: Mapped[str] = mapped_column(String(100), nullable=False)
    es_correcta: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fecha_evento: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
