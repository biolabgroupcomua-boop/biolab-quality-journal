import enum

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models._mixins import RecordMixin


class SpecificationStatusEnum(str, enum.Enum):
    """Статус специфікації.

    - DRAFT — чернетка, можна редагувати
    - APPROVED — затверджено, редагувати НЕ можна (тільки створити v1.1)
    - NEEDS_VERIFICATION — норми витягнуті з історії варок, потребує
      перевірки технологом перед затвердженням
    """

    DRAFT = "draft"
    APPROVED = "approved"
    NEEDS_VERIFICATION = "needs_verification"


class Specification(Base, RecordMixin):
    """Норми на рецептуру (RP). Затверджуються технологом.

    Числові норми (pH min/max) використовуються для обчислення verdict OK/OUT
    у `BulkBatch`. Рядкові норми (в'язкість, густина як рядок діапазону)
    переносяться в паспорт як є — порівняти числово неможливо.
    """

    __tablename__ = "specifications"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)

    spec_id: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    version: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[SpecificationStatusEnum] = mapped_column(
        Enum(SpecificationStatusEnum), nullable=False, default=SpecificationStatusEnum.DRAFT
    )

    # текстові норми (показники органолептики)
    appearance: Mapped[str | None] = mapped_column(nullable=True)
    color: Mapped[str | None] = mapped_column(nullable=True)
    smell: Mapped[str | None] = mapped_column(nullable=True)

    # числові норми (для автоматичного OK/OUT)
    ph_min: Mapped[float | None] = mapped_column(nullable=True)
    ph_max: Mapped[float | None] = mapped_column(nullable=True)

    # рядкові норми (в'язкість/густина як діапазон — порівнюємо людиною)
    viscosity_norm: Mapped[str | None] = mapped_column(nullable=True)
    density_norm: Mapped[str | None] = mapped_column(nullable=True)
    colloid_norm: Mapped[str | None] = mapped_column(nullable=True)
    thermo_norm: Mapped[str | None] = mapped_column(nullable=True)
    micro_total_norm: Mapped[str | None] = mapped_column(nullable=True)
    micro_yeast_norm: Mapped[str | None] = mapped_column(nullable=True)

    storage_conditions: Mapped[str | None] = mapped_column(nullable=True)
    shelf_life_months: Mapped[int | None] = mapped_column(nullable=True)
    pao_months: Mapped[int | None] = mapped_column(nullable=True)

    source: Mapped[str | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(nullable=True)

    product: Mapped["Product"] = relationship(back_populates="specifications")  # noqa: F821
    bulk_batches: Mapped[list["BulkBatch"]] = relationship(  # noqa: F821
        back_populates="specification"
    )

    def __repr__(self) -> str:
        return f"<Specification {self.spec_id} status={self.status.value}>"
