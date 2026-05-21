from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models._mixins import RecordMixin


class ProductVariant(Base, RecordMixin):
    """Товарна позиція = ТМ × RP × етикетка.

    Приклад: Crumb продає наш RP032 як "Гель для душу Chery and Santal, 200 ml".
    Pinky може продавати той самий RP032 як "Гель Floral wood".

    `product_id` може бути NULL для товарів у розробці (ще не присвоєно RP).
    Паспорт згенерувати на такий варіант не можна.
    """

    __tablename__ = "product_variants"

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"), nullable=True, index=True
    )

    label_name: Mapped[str] = mapped_column(nullable=False)
    packaging_type: Mapped[str | None] = mapped_column(nullable=True)
    packaging_volume_ml: Mapped[float | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="variants")  # noqa: F821
    product: Mapped["Product | None"] = relationship(back_populates="variants")  # noqa: F821
    finished_batches: Mapped[list["FinishedBatch"]] = relationship(  # noqa: F821
        back_populates="variant"
    )

    def __repr__(self) -> str:
        return f"<ProductVariant {self.label_name!r} for customer_id={self.customer_id}>"
