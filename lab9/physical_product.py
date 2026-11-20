from can_be_shipped import CanBeShipped
from math import isfinite
from product import Product
from product_record import ProductRecord
from supplier import Supplier, UNKNOWN_SUPPLIER, supplier_from_record


class PhysicalProduct(Product, CanBeShipped):

    def __init__(self, product_id: str, name: str, price: float, stock: int, weight: float, history: list[int] | None = None, *, supplier: Supplier = UNKNOWN_SUPPLIER) -> None:
        super().__init__(product_id, name, price, stock, history, supplier=supplier)
        weight = float(weight)
        if not isfinite(weight) or weight < 0:
            raise ValueError("Weight must be a non-negative finite number.")
        self.__weight = weight

    @property
    def weight(self) -> float:
        return self.__weight

    def display_information(self) -> None:
        super().display_information()
        print("Type: Physical")
        print(f"Weight: {self.__weight:g} kg")
        print(f"Shipping Cost: ${self.calculate_shipping_cost():.2f}")
        print("Fulfilment:", self.get_fulfilment_info())

    def get_fulfilment_info(self) -> str:
        return "Requires physical shipping."

    def calculate_shipping_cost(self) -> float:
        return round(self.__weight * 5.0, 2)

    def to_dict(self) -> ProductRecord:
        data = super().to_dict()
        data["type"] = "physical"
        data["weight"] = self.__weight
        return data

    @classmethod
    def from_dict(cls, data: ProductRecord, supplier: Supplier | None = None) -> 'PhysicalProduct':
        return super().from_dict(data, supplier or supplier_from_record(data), weight=data["weight"])
