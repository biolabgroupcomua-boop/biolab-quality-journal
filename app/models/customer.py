from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models._mixins import RecordMixin


class Customer(Base, RecordMixin):
    """ТМ-замовник: клієнт-власник торгової марки.

    Приклади: Crumb, Plis Me, Pinky, Пухтенко, Азаренко, ANKIE002.
    """

    __tablename__ = "customers"

    trademark_name: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    contact_person: Mapped[str | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(nullable=True)

    # зворотні зв'язки
    variants: Mapped[list["ProductVariant"]] = relationship(  # noqa: F821
        back_populates="customer", cascade="all"
    )

    def __repr__(self) -> str:
        return f"<Customer {self.trademark_name!r}>"
