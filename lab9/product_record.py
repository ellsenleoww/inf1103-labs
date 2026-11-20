from typing import NotRequired, TypedDict
from supplier_record import SupplierRecord


class ProductRecord(TypedDict):
    id: str
    name: str
    price: float
    stock: int
    history: NotRequired[list[int]]
    type: NotRequired[str]
    weight: NotRequired[float]
    download_size: NotRequired[float]
    supplier: NotRequired[SupplierRecord]
