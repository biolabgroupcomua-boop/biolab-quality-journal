from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models._mixins import RecordMixin


class Product(Base, RecordMixin):
    """RP-артикул — наша внутрішня рецептура.

    Приклади: RP001 (Шампунь Anti-Dundruff), RP032 (Гель для душу),
    L301 (Тонік Rich). Один RP = одна рецептура.
    """

    __tablename__ = "products"

    rp_code: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    internal_name: Mapped[str] = mapped_column(nullable=False)
    category: Mapped[str | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(nullable=True)

    # зворотні зв'язки
    variants: Mapped[list["ProductVariant"]] = relationship(  # noqa: F821
        back_populates="product"
    )
    specifications: Mapped[list["Specification"]] = relationship(  # noqa: F821
        back_populates="product", cascade="all"
    )
    bulk_batches: Mapped[list["BulkBatch"]] = relationship(  # noqa: F821
        back_populates="product"
    )

    def __repr__(self) -> str:
        return f"<Product {self.rp_code} {self.internal_name!r}>"
