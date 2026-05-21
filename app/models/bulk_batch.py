import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models._mixins import RecordMixin


class VerdictEnum(str, enum.Enum):
    """Висновок по варці — обчислюється автоматично у verdict_calculator."""

    OK = "ok"
    OUT = "out"


class BulkBatch(Base, RecordMixin):
    """Варка напівфабрикату (bulk партія).

    Технолог вводить тільки факт-показники. Норми не дублюються —
    тягнуться з пов'язаної `Specification`. Висновок `verdict` рахується
    автоматично з порівняння факт vs норма.
    """

    __tablename__ = "bulk_batches"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    specification_id: Mapped[int] = mapped_column(
        ForeignKey("specifications.id"), nullable=False, index=True
    )

    batch_number: Mapped[str] = mapped_column(nullable=False, index=True)
    date_mfg: Mapped[date] = mapped_column(Date, nullable=False)
    volume_kg: Mapped[float | None] = mapped_column(nullable=True)

    # органолептика (текстова)
    appearance_fact: Mapped[str | None] = mapped_column(nullable=True)
    color_fact: Mapped[str | None] = mapped_column(nullable=True)
    smell_fact: Mapped[str | None] = mapped_column(nullable=True)

    # числові факти
    ph_fact: Mapped[float | None] = mapped_column(nullable=True)
    density_fact: Mapped[float | None] = mapped_column(nullable=True)

    # рядкові факти (в'язкість як вираз "S3V12 Cp=7667 mPas")
    viscosity_fact: Mapped[str | None] = mapped_column(nullable=True)
    viscosity_unit: Mapped[str | None] = mapped_column(nullable=True)
    colloid_fact: Mapped[str | None] = mapped_column(nullable=True)
    thermo_fact: Mapped[str | None] = mapped_column(nullable=True)
    micro_total_fact: Mapped[str | None] = mapped_column(nullable=True)
    micro_yeast_fact: Mapped[str | None] = mapped_column(nullable=True)

    operator: Mapped[str | None] = mapped_column(nullable=True)
    arbitrary_samples_taken: Mapped[bool] = mapped_column(default=False, nullable=False)
    verdict: Mapped[VerdictEnum] = mapped_column(
        Enum(VerdictEnum), nullable=False, default=VerdictEnum.OK
    )
    notes: Mapped[str | None] = mapped_column(nullable=True)

    product: Mapped["Product"] = relationship(back_populates="bulk_batches")  # noqa: F821
    specification: Mapped["Specification"] = relationship(  # noqa: F821
        back_populates="bulk_batches"
    )
    finished_batches: Mapped[list["FinishedBatch"]] = relationship(  # noqa: F821
        back_populates="bulk_batch"
    )

    def __repr__(self) -> str:
        return f"<BulkBatch {self.batch_number} verdict={self.verdict.value}>"
