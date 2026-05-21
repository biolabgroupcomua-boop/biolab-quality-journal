import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models._mixins import RecordMixin


class CertificateStatusEnum(str, enum.Enum):
    CREATED = "created"
    REVOKED = "revoked"


class QualityCertificate(Base, RecordMixin):
    """Паспорт якості (CoA) на партію готової продукції.

    Генерується кнопкою з `FinishedBatch`. Усі поля паспорта обчислюються
    з пов'язаних сутностей; вручну можна заповнити лише `verdict_text`.
    """

    __tablename__ = "quality_certificates"

    finished_batch_id: Mapped[int] = mapped_column(
        ForeignKey("finished_batches.id"), nullable=False, index=True
    )

    passport_no: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    pdf_path: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[CertificateStatusEnum] = mapped_column(
        Enum(CertificateStatusEnum), nullable=False, default=CertificateStatusEnum.CREATED
    )
    verdict_text: Mapped[str | None] = mapped_column(nullable=True)

    finished_batch: Mapped["FinishedBatch"] = relationship(  # noqa: F821
        back_populates="certificates"
    )

    def __repr__(self) -> str:
        return f"<QualityCertificate {self.passport_no} status={self.status.value}>"
