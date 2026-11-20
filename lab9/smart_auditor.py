from input_helpers import get_positive_float, get_nonnegative_float, get_integer
from product_factory import ProductFactory
import json
import tempfile
import os
from supplier_record import SupplierRecord
from product_record import ProductRecord
from supplier import Supplier
from product import Product
from can_be_shipped import CanBeShipped
from physical_product import PhysicalProduct
from digital_product import DigitalProduct
from order_line import OrderLine
from order import Order
from inventory import Inventory
from supplier import UNKNOWN_SUPPLIER, supplier_from_record


def product_from_dict(data: ProductRecord, suppliers: dict[str, Supplier] | None = None) -> 'Product':
    supplier = supplier_from_record(data)
    if suppliers is not None:
        shared = suppliers.setdefault(supplier.supplier_id, supplier)
        if shared != supplier:
            raise ValueError(f"Conflicting supplier details for {supplier.supplier_id}")
        supplier = shared
    return ProductFactory.from_record(data, supplier)



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
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=".", prefix="inventory_", suffix=".tmp", delete=False) as file:
            temporary = file.name
            json.dump(records, file, indent=4, allow_nan=False)
        os.replace(temporary, "inventory.json")
        temporary = None
    finally:
        if temporary is not None:
            os.unlink(temporary)
    print("Inventory saved successfully to inventory.json.")


def display_all(inventory: Inventory) -> None:
    inventory.display_all()


def add_product(inventory: Inventory, supplier: Supplier = UNKNOWN_SUPPLIER) -> None:
    print("\nAdd New Product")
    product_id = input("Product ID: ")
    if inventory.find_product(product_id) is not None:
        print("Product ID already exists.")
        return
    print("1. Physical Product")
    print("2. Digital Product")
    while True:
        product_type = input("Product Type (1 or 2): ")
        if product_type in ("1", "2"):
            break
        print("Invalid product type. Please choose 1 or 2.")
    name = input("Product Name: ")
    price = get_positive_float("Price: ")
    stock = get_integer("Stock Quantity: ")
    if product_type == "1":
        weight = get_nonnegative_float("Weight (kg): ")
        product = ProductFactory.create("physical", product_id, name, price, stock, supplier, weight=weight)
    else:
        download_size = get_nonnegative_float("Download Size (MB): ")
        product = ProductFactory.create("digital", product_id, name, price, stock, supplier, download_size=download_size)
    inventory.add_product(product)
    print("\nProduct added successfully!")


def update_stock(inventory: Inventory) -> None:
    print("\nUpdate Stock")
    product = inventory.find_product(input("Enter Product ID: "))
    if product is None:
        print("\nProduct not found.")
        return
    print("\nProduct Found:")
    print("Name:", product.name)
    print("Current Stock:", product.stock)
    inventory.update_stock(product.product_id, get_integer("\nNew Stock Quantity: "))
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


def add_supplied_product(inventory: Inventory) -> None:
    supplier_id = input("Supplier ID: ").strip()
    if not supplier_id:
        print("Enter a supplier ID.")
        return
    for product in inventory.get_products():
        if product.supplier.supplier_id == supplier_id:
            add_product(inventory, product.supplier)
            return
    supplier = Supplier(supplier_id, input("Supplier name: "), input("Contact email: "))
    add_product(inventory, supplier)


def enter_order(inventory: Inventory, order: Order) -> None:
    while True:
        product_id = input("Product ID (blank to finish): ")
        if not product_id:
            break
        product = inventory.find_product(product_id)
        if product is None:
            print("Product not found.")
            continue
        quantity = get_integer("Order quantity: ", 1)
        order.add_order_line(product, quantity)
    order.display_information()


def main() -> None:
    print("========================================")
    print("INVENTORY MANAGEMENT SYSTEM")
    print("========================================")

    try:
        inventory = load_inventory()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Could not load inventory: {error}")
        return
    orders: dict[str, Order] = {}

    while True:
        print("\n---------- MENU ----------")
        print("1. Display All Products")
        print("2. Add Product")
        print("3. Update Stock")
        print("4. Search Product")
        print("5. Save Inventory")
        print("6. Exit")
        print("7. Add Product with Supplier")
        print("8. Remove Product")
        print("9. Create or Display Order")
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
            try:
                save_inventory(inventory)
            except (OSError, ValueError) as error:
                print(f"Could not save inventory: {error}")
                continue
        elif option == "6":
            print("\nSaving inventory before exit...")
            try:
                save_inventory(inventory)
            except (OSError, ValueError) as error:
                print(f"Could not save inventory: {error}")
                continue
            print("\nThank you for using Inventory Management System.")
            print("Program terminated.")
            break
        elif option == "7":
            add_supplied_product(inventory)
        elif option == "8":
            removed = inventory.remove_product(input("Product ID: "))
            print("Product removed." if removed else "Product not found.")
        elif option == "9":
            order_id = input("Order ID: ").strip()
            if not order_id:
                print("Enter an order ID.")
            elif order_id in orders:
                orders[order_id].display_information()
            else:
                order = Order(order_id)
                enter_order(inventory, order)
                orders[order_id] = order
        else:
            print("Invalid option. Please choose 1 to 9.")


if __name__ == "__main__":
    main()
