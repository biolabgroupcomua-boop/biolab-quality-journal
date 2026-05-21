"""SQLAlchemy моделі застосунку.

Імпорти тут потрібні, щоб Alembic autogenerate бачив усі моделі
через `from app.models import *`.
"""

from app.models._mixins import RecordMixin
from app.models.bulk_batch import BulkBatch, VerdictEnum
from app.models.certificate import CertificateStatusEnum, QualityCertificate
from app.models.customer import Customer
from app.models.finished_batch import FinishedBatch
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.specification import Specification, SpecificationStatusEnum

__all__ = [
    "RecordMixin",
    "Customer",
    "Product",
    "ProductVariant",
    "Specification",
    "SpecificationStatusEnum",
    "BulkBatch",
    "VerdictEnum",
    "FinishedBatch",
    "QualityCertificate",
    "CertificateStatusEnum",
]
