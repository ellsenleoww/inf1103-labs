from abc import ABC, abstractmethod
from supplier import Supplier, UNKNOWN_SUPPLIER
from supplier_record import SupplierRecord
from product_record import ProductRecord


class Product(ABC):

    def __init__(self, product_id: str, name: str, price: float, stock: int, history: list[int] | None = None, *, supplier: Supplier = UNKNOWN_SUPPLIER) -> None:
        self.__supplier: Supplier = supplier
        self.__product_id = product_id
        self.__name = name
        self.__price = price
        self.__stock = stock
        self.__history: list[int] | None = [stock] if history is None else list(history)

    @property
    def supplier(self) -> Supplier:
        return self.__supplier

    @property
    def product_id(self) -> str:
        return self.__product_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def price(self) -> float:
        return self.__price

    @property
    def stock(self) -> int:
        return self.__stock

    @property
    def history(self) -> list[int]:
        return [] if self.__history is None else self.__history.copy()

    def update_stock(self, quantity: int) -> None:
        transaction = quantity - self.__stock
        self.__stock = quantity

        if self.__history is None:
            self.__history = []
        self.__history.append(transaction)

    def display_information(self) -> None:
        print("ID:", self.__product_id)
        print("Name:", self.__name)
        print(f"Price: ${self.__price:.2f}")
        print("Stock:", self.__stock)
        self.supplier.display_information()

    def display_summary(self) -> None:
        print(
            f"ID: {self.__product_id} | "
            f"Name: {self.__name} | "
            f"Price: ${self.__price:.2f} | "
            f"Stock: {self.__stock}"
        )

    @abstractmethod
    def get_fulfilment_info(self) -> str:
        pass

    def to_dict(self) -> ProductRecord:
        data: ProductRecord = {
            "id": self.__product_id,
            "name": self.__name,
            "price": self.__price,
            "stock": self.__stock,
        }
        if self.__history is not None:
            data["history"] = self.__history.copy()
        if self.supplier != UNKNOWN_SUPPLIER:
            data["supplier"] = SupplierRecord(supplier_id=self.supplier.supplier_id, name=self.supplier.name, contact_email=self.supplier.contact_email)
        return data

    @classmethod
    def from_dict(cls, data: ProductRecord, supplier: Supplier = UNKNOWN_SUPPLIER, **extra_attributes: float) -> 'Product':
        product = cls(
            data["id"], data["name"], data["price"], data["stock"],
            history=data.get("history", []),
            supplier=supplier, **extra_attributes,
        )
        if "history" not in data:
            product.__history = None
        return product
