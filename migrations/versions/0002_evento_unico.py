"""lms_interactions: un evento de Moodle, una fila

Cada sincronización volvía a insertar las mismas interacciones: la tabla no
tenía nada que impidiera repetir ``moodle_event_id`` (usuario-cmid) y el
adaptador siempre hacía INSERT. En el entorno local los tres cursos del MVP
habían acumulado cinco copias de cada fila. Con la sincronización programada de
la nube, eso crece sin techo.

Esta revisión borra las repeticiones —se queda con la más reciente de cada
evento, que es la que trae la nota actualizada— y crea el índice único que
sostiene el UPSERT del adaptador.

Revision ID: 0002_evento_unico
Revises: 0001_baseline
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_evento_unico"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDICE = "uq_lms_interactions_moodle_event_id"


def upgrade() -> None:
    # De cada evento repetido se conserva la fila más reciente por fecha_evento
    # (y, a igualdad, la de mayor id) porque es la que refleja la última nota.
    op.execute(
        sa.text(
            """
            DELETE FROM lms_interactions a
             USING lms_interactions b
             WHERE a.moodle_event_id IS NOT NULL
               AND a.moodle_event_id = b.moodle_event_id
               AND (a.fecha_evento, a.id) < (b.fecha_evento, b.id)
            """
        )
    )
    op.create_index(INDICE, "lms_interactions", ["moodle_event_id"], unique=True)


def downgrade() -> None:
    op.drop_index(INDICE, table_name="lms_interactions")
