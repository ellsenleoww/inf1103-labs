import json
import os
from dataclasses import dataclass
from typing import NotRequired, TypedDict
from abc import ABC, abstractmethod
from math import isfinite


class SupplierRecord(TypedDict):
    supplier_id: str
    name: str
    contact_email: str


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


@dataclass(frozen=True)
class Supplier:
    supplier_id: str
    name: str
    contact_email: str

    def display_information(self) -> None:
        print("Supplier ID:", self.supplier_id)
        print("Supplier:", self.name)
        print("Contact email:", self.contact_email)


UNKNOWN_SUPPLIER = Supplier("", "Supplier not recorded", "")


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


class CanBeShipped(ABC):

    @abstractmethod
    def calculate_shipping_cost(self) -> float:
        pass


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


@dataclass(frozen=True)
class OrderLine:
    product: Product
    quantity: int

    def calculate_subtotal(self) -> float:
        return self.product.price * self.quantity


class Order:
    def __init__(self, order_id: str) -> None:
        self.order_id: str = order_id
        self.__order_lines: list[OrderLine] = []

    @property
    def order_lines(self) -> tuple[OrderLine, ...]:
        return tuple(self.__order_lines)

    def add_order_line(self, product: Product, quantity: int) -> None:
        if type(quantity) is not int or quantity < 1:
            raise ValueError("Order quantity must be a positive integer.")
        self.__order_lines.append(OrderLine(product, quantity))

    def remove_order_line(self, index: int) -> None:
        if not 0 <= index < len(self.__order_lines):
            raise IndexError("Order line index out of range.")
        del self.__order_lines[index]

    def calculate_total(self) -> float:
        return sum((line.calculate_subtotal() for line in self.__order_lines), 0.0)

    def display_information(self) -> None:
        print("Order:", self.order_id)
        for line in self.__order_lines:
            print(f"{line.product.name} x {line.quantity}: ${line.calculate_subtotal():.2f}")
        print(f"Total: ${self.calculate_total():.2f}")


class Inventory:

    def __init__(self) -> None:
        self.__products: list[Product] = []

    def add_product(self, product: Product) -> bool:
        if self.search_product(product.product_id) is not None:
            return False
        self.__products.append(product)
        return True

    def remove_product(self, product_id: str) -> Product | None:
        product = self.find_product(product_id)
        if product is not None:
            self.__products.remove(product)
        return product

    def search_product(self, product_id: str) -> Product | None:
        return self.find_product(product_id)

    def find_product(self, product_id: str) -> Product | None:
        for product in self.__products:
            if product.product_id == product_id:
                return product
        return None

    def update_stock(self, product_id: str, quantity: int) -> bool:
        product = self.search_product(product_id)
        if product is None:
            return False
        product.update_stock(quantity)
        return True

    def get_products(self) -> tuple[Product, ...]:
        return tuple(self.__products)

    def display_all(self) -> None:
        print("\nCurrent Inventory")
        print("----------------------------------------")

        if len(self.__products) == 0:
            print("Inventory is empty.")
        else:
            for index, product in enumerate(self.__products):
                if index > 0:
                    print()
                product.display_information()

        print("----------------------------------------")


def supplier_from_record(data: ProductRecord) -> Supplier:
    record = data.get("supplier")
    return Supplier(**record) if record is not None else UNKNOWN_SUPPLIER


def product_from_dict(data: ProductRecord, suppliers: dict[str, Supplier] | None = None) -> 'Product':
    supplier = supplier_from_record(data)
    if suppliers is not None:
        shared = suppliers.setdefault(supplier.supplier_id, supplier)
        if shared != supplier:
            raise ValueError(f"Conflicting supplier details for {supplier.supplier_id}")
        supplier = shared
    if "type" not in data:
        data = dict(data, type="physical", weight=0.0)

    if data["type"] == "physical":
        return PhysicalProduct.from_dict(data, supplier)
    if data["type"] == "digital":
        return DigitalProduct.from_dict(data, supplier)
    raise ValueError(f"Unknown product type in inventory.json: {data['type']!r}")


def load_inventory() -> Inventory:
    inventory = Inventory()
    if os.path.exists("inventory.json"):
        print("inventory.json found.")

        with open("inventory.json", "r") as file:
            records = json.load(file)

        suppliers: dict[str, Supplier] = {}
        for record in records:
            product = product_from_dict(record, suppliers)
            if not inventory.add_product(product):
                raise ValueError(
                    f"Duplicate Product ID in inventory.json: {product.product_id}"
                )

        print("Inventory loaded successfully.")
    else:
        print("inventory.json not found.")
        print("Starting with an empty inventory.")

    return inventory


def save_inventory(inventory: Inventory) -> None:
    records = [product.to_dict() for product in inventory.get_products()]
    with open("inventory.json", "w") as file:
        json.dump(records, file, indent=4)

    print("Inventory saved successfully to inventory.json.")


def display_all(inventory: Inventory) -> None:
    inventory.display_all()


def add_product(inventory: Inventory) -> None:
    print("\nAdd New Product")
    product_id = input("Product ID: ")

    if inventory.search_product(product_id) is not None:
        print("Product ID already exists.")
        return

    print("1. Physical Product")
    print("2. Digital Product")
    product_type = input("Product Type (1 or 2): ")
    if product_type not in ("1", "2"):
        print("Invalid product type. Please choose 1 or 2.")
        return

    name = input("Product Name: ")
    try:
        price = float(input("Price: "))
        stock = int(input("Stock Quantity: "))
        if product_type == "1":
            weight = float(input("Weight (kg): "))
            product = PhysicalProduct(product_id, name, price, stock, weight)
        else:
            download_size = float(input("Download Size (MB): "))
            product = DigitalProduct(product_id, name, price, stock, download_size)
    except ValueError as error:
        print(f"Invalid product details: {error}")
        return

    if inventory.add_product(product):
        print("\nProduct added successfully!")
    else:
        print("Product ID already exists.")


def update_stock(inventory: Inventory) -> None:
    print("\nUpdate Stock")
    product_id = input("Enter Product ID: ")
    product = inventory.search_product(product_id)

    if product is None:
        print("\nProduct not found.")
        return

    print("\nProduct Found:")
    print("Name:", product.name)
    print("Current Stock:", product.stock)

    try:
        new_stock = int(input("\nNew Stock Quantity: "))
    except ValueError:
        print("Stock quantity must be an integer.")
        return
    inventory.update_stock(product_id, new_stock)
    print("\nStock updated successfully!")


def search_product(inventory: Inventory) -> None:
    print("\nSearch Product")
    product_id = input("Enter Product ID: ")
    product = inventory.search_product(product_id)

    if product is None:
        print("\nProduct not found.")
        return

    print("\nProduct Found")
    print("----------------------------------------")
    product.display_information()
    print("----------------------------------------")


def main() -> None:
    print("========================================")
    print("INVENTORY MANAGEMENT SYSTEM")
    print("========================================")

    inventory = load_inventory()

    while True:
        print("\n---------- MENU ----------")
        print("1. Display All Products")
        print("2. Add Product")
        print("3. Update Stock")
        print("4. Search Product")
        print("5. Save Inventory")
        print("6. Exit")
        print("--------------------------")

        option = input("\nEnter option: ")

        if option == "1":
            display_all(inventory)
        elif option == "2":
            add_product(inventory)
        elif option == "3":
            update_stock(inventory)
        elif option == "4":
            search_product(inventory)
        elif option == "5":
            print("\nSaving inventory...")
            save_inventory(inventory)
        elif option == "6":
            print("\nSaving inventory before exit...")
            save_inventory(inventory)
            print("\nThank you for using Inventory Management System.")
            print("Program terminated.")
            break
        else:
            print("\nInvalid option. Please choose 1 to 6.")


if __name__ == "__main__":
    main()