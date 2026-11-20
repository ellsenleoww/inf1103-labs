from math import isfinite
from product import Product
from product_record import ProductRecord
from supplier import Supplier, UNKNOWN_SUPPLIER, supplier_from_record


class DigitalProduct(Product):

    def __init__(self, product_id: str, name: str, price: float, stock: int, download_size: float, history: list[int] | None = None, *, supplier: Supplier = UNKNOWN_SUPPLIER) -> None:
        super().__init__(product_id, name, price, stock, history, supplier=supplier)
        download_size = float(download_size)
        if not isfinite(download_size) or download_size < 0:
            raise ValueError("Download size must be a non-negative finite number.")
        self.__download_size = download_size

    @property
    def download_size(self) -> float:
        return self.__download_size

    def display_information(self) -> None:
        super().display_information()
        print("Type: Digital")
        print(f"Download Size: {self.__download_size:g} MB")
        print("Fulfilment:", self.get_fulfilment_info())

    def get_fulfilment_info(self) -> str:
        return "Delivered digitally by download."

    def to_dict(self) -> ProductRecord:
        data = super().to_dict()
        data["type"] = "digital"
        data["download_size"] = self.__download_size
        return data

    @classmethod
    def from_dict(cls, data: ProductRecord, supplier: Supplier | None = None) -> 'DigitalProduct':
        return super().from_dict(data, supplier or supplier_from_record(data), download_size=data["download_size"])
