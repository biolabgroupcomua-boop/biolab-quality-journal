from datetime import date

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models._mixins import RecordMixin


class FinishedBatch(Base, RecordMixin):
    """Партія готової продукції — фасування варки під конкретний варіант.

    Фіз-хім показники тут не дублюються — паспорт читає їх з пов'язаної
    `BulkBatch`. `allowed_for_shipment` обчислюється з `bulk_batch.verdict`.
    """

    __tablename__ = "finished_batches"

    bulk_batch_id: Mapped[int] = mapped_column(
        ForeignKey("bulk_batches.id"), nullable=False, index=True
    )
    product_variant_id: Mapped[int] = mapped_column(
        ForeignKey("product_variants.id"), nullable=False, index=True
    )

    batch_number_gp: Mapped[str] = mapped_column(nullable=False, index=True)
    date_filling: Mapped[date] = mapped_column(Date, nullable=False)
    date_aroma_added: Mapped[date | None] = mapped_column(Date, nullable=True)
    quantity_units: Mapped[int | None] = mapped_column(nullable=True)

    allowed_for_shipment: Mapped[bool] = mapped_column(default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(nullable=True)

    bulk_batch: Mapped["BulkBatch"] = relationship(back_populates="finished_batches")  # noqa: F821
    variant: Mapped["ProductVariant"] = relationship(  # noqa: F821
        back_populates="finished_batches"
    )
    certificates: Mapped[list["QualityCertificate"]] = relationship(  # noqa: F821
        back_populates="finished_batch"
    )

    def __repr__(self) -> str:
        return f"<FinishedBatch {self.batch_number_gp}>"
