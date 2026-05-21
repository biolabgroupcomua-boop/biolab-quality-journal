from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class RecordMixin:
    """Спільні поля для всіх моделей: id, timestamps, soft delete.

    Soft delete: ніяких DELETE FROM. Замість цього — is_deleted=True
    + причина + дата (це залізне правило з CLAUDE.md).
    """

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    deleted_reason: Mapped[str | None] = mapped_column(nullable=True)
