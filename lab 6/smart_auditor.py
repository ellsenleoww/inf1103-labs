import json
import os


class Product:
    """Represent one product and control changes to its stock and history."""

    def __init__(self, product_id, name, price, stock, history=None):
        self.__product_id = product_id
        self.__name = name
        self.__price = price
        self.__stock = stock
        self.__history = [stock] if history is None else list(history)

    @property
    def product_id(self):
        return self.__product_id

    @property
    def name(self):
        return self.__name

    @property
    def price(self):
        return self.__price

    @property
    def stock(self):
        return self.__stock

    @property
    def history(self):
        return [] if self.__history is None else self.__history.copy()

    def update_stock(self, quantity):
        """Set the new total stock and record the change, including zero."""
        transaction = quantity - self.__stock
        self.__stock = quantity

        if self.__history is None:
            self.__history = []
        self.__history.append(transaction)

    def display_information(self):
        """Display the same product details as the Week 5 search operation."""
        print("ID:", self.__product_id)
        print("Name:", self.__name)
        print(f"Price: ${self.__price:.2f}")
        print("Stock:", self.__stock)

    def display_summary(self):
        """Display one row for the inventory listing."""
        print(
            f"ID: {self.__product_id} | "
            f"Name: {self.__name} | "
            f"Price: ${self.__price:.2f} | "
            f"Stock: {self.__stock}"
        )

    def to_dict(self):
        """Return product data in the Week 5 format; perform no file I/O."""
        data = {
            "id": self.__product_id,
            "name": self.__name,
            "price": self.__price,
            "stock": self.__stock,
        }

        if self.__history is not None:
            data["history"] = self.__history.copy()
        return data

    @classmethod
    def from_dict(cls, data):
        """Recreate a product without adding a new opening transaction."""
        product = cls(
            data["id"], data["name"], data["price"], data["stock"],
            history=data.get("history", []),
        )
        if "history" not in data:
            product.__history = None
        return product


class Inventory:
    """Manage a collection of Product objects, without input or file I/O."""

    def __init__(self):
        self.__products = []

    def add_product(self, product):
        """Add a product only when its ID is unique; report success."""
        if self.search_product(product.product_id) is not None:
            return False
        self.__products.append(product)
        return True

    def search_product(self, product_id):
        for product in self.__products:
            if product.product_id == product_id:
                return product
        return None

    def update_stock(self, product_id, quantity):
        """Find the product and let it manage its own stock change."""
        product = self.search_product(product_id)
        if product is None:
            return False
        product.update_stock(quantity)
        return True

    def get_products(self):
        """Provide a snapshot that cannot add/remove internal list entries."""
        return tuple(self.__products)

    def display_all(self):
        print("\nCurrent Inventory")
        print("----------------------------------------")

        if len(self.__products) == 0:
            print("Inventory is empty.")
        else:
            for product in self.__products:
                product.display_summary()

        print("----------------------------------------")


def load_inventory():
    """Load the original JSON list and convert its records into objects."""
    inventory = Inventory()
    if os.path.exists("inventory.json"):
        print("inventory.json found.")

        with open("inventory.json", "r") as file:
            records = json.load(file)

        for record in records:
            product = Product.from_dict(record)
            if not inventory.add_product(product):
                raise ValueError(
                    f"Duplicate Product ID in inventory.json: {product.product_id}"
                )

        print("Inventory loaded successfully.")
    else:
        print("inventory.json not found.")
        print("Starting with an empty inventory.")

    return inventory


def save_inventory(inventory):
    """Save objects as the same list of dictionaries used in Week 5."""
    records = [product.to_dict() for product in inventory.get_products()]
    with open("inventory.json", "w") as file:
        json.dump(records, file, indent=4)

    print("Inventory saved successfully to inventory.json.")


def display_all(inventory):
    inventory.display_all()


def add_product(inventory):
    print("\nAdd New Product")
    product_id = input("Product ID: ")

    if inventory.search_product(product_id) is not None:
        print("Product ID already exists.")
        return

    name = input("Product Name: ")
    price = float(input("Price: "))
    stock = int(input("Stock Quantity: "))

    product = Product(product_id, name, price, stock)
    if inventory.add_product(product):
        print("\nProduct added successfully!")
    else:
        print("Product ID already exists.")


def update_stock(inventory):
    print("\nUpdate Stock")
    product_id = input("Enter Product ID: ")
    product = inventory.search_product(product_id)

    if product is None:
        print("\nProduct not found.")
        return

    print("\nProduct Found:")
    print("Name:", product.name)
    print("Current Stock:", product.stock)

    new_stock = int(input("\nNew Stock Quantity: "))
    inventory.update_stock(product_id, new_stock)
    print("\nStock updated successfully!")


def search_product(inventory):
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


def main():
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