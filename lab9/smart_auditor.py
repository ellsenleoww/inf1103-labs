from product_factory import ProductFactory
import json
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
    with open("inventory.json", "w") as file:
        json.dump(records, file, indent=4)

    print("Inventory saved successfully to inventory.json.")


def display_all(inventory: Inventory) -> None:
    inventory.display_all()


def add_product(inventory: Inventory, supplier: Supplier = UNKNOWN_SUPPLIER) -> None:
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
            product = ProductFactory.create("physical", product_id, name, price, stock, supplier, weight=weight)
        else:
            download_size = float(input("Download Size (MB): "))
            product = ProductFactory.create("digital", product_id, name, price, stock, supplier, download_size=download_size)
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
        try:
            order.add_order_line(product, int(input("Order quantity: ")))
        except ValueError:
            print("Enter a positive whole number.")
    order.display_information()


def main() -> None:
    print("========================================")
    print("INVENTORY MANAGEMENT SYSTEM")
    print("========================================")

    inventory = load_inventory()
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
            save_inventory(inventory)
        elif option == "6":
            print("\nSaving inventory before exit...")
            save_inventory(inventory)
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
