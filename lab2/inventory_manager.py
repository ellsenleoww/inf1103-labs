import json
import os

def load_inventory():
    if os.path.exists("inventory.json"):
        print("inventory.json found.")

        with open("inventory.json", "r") as file:
            inventory = json.load(file)

        print("Inventory loaded successfully.")
        return inventory

    else:
        print("inventory.json not found.")
        print("Starting with an empty inventory.")
        return []


def save_inventory(inventory):
    with open("inventory.json", "w") as file:
        json.dump(inventory, file, indent=4)

    print("Inventory saved successfully to inventory.json.")


def display_all(inventory):
    print("\nCurrent Inventory")
    print("----------------------------------------")

    if len(inventory) == 0:
        print("Inventory is empty.")

    else:
        for product in inventory:
            print(
                f"ID: {product['id']} | "
                f"Name: {product['name']} | "
                f"Price: ${product['price']:.2f} | "
                f"Stock: {product['stock']}"
            )

    print("----------------------------------------")


def add_product(inventory):
    print("\nAdd New Product")

    product_id = input("Product ID: ")

    # Check if ID already exists
    for product in inventory:
        if product["id"] == product_id:
            print("Product ID already exists.")
            return

    name = input("Product Name: ")
    price = float(input("Price: "))
    stock = int(input("Stock Quantity: "))

    new_product = {
        "id": product_id,
        "name": name,
        "price": price,
        "stock": stock,
        "history": [stock]
    }

    inventory.append(new_product)

    print("\nProduct added successfully!")


def update_stock(inventory):
    print("\nUpdate Stock")

    product_id = input("Enter Product ID: ")

    for product in inventory:
        if product["id"] == product_id:

            print("\nProduct Found:")
            print("Name:", product["name"])
            print("Current Stock:", product["stock"])

            new_stock = int(input("\nNew Stock Quantity: "))

            # Calculate the transaction amount
            transaction = new_stock - product["stock"]

            product["stock"] = new_stock

            # Make sure history exists
            if "history" not in product:
                product["history"] = []

            product["history"].append(transaction)

            print("\nStock updated successfully!")
            return

    print("\nProduct not found.")


def search_product(inventory):
    print("\nSearch Product")

    product_id = input("Enter Product ID: ")

    for product in inventory:
        if product["id"] == product_id:

            print("\nProduct Found")
            print("----------------------------------------")
            print("ID:", product["id"])
            print("Name:", product["name"])
            print(f"Price: ${product['price']:.2f}")
            print("Stock:", product["stock"])
            print("----------------------------------------")

            return

    print("\nProduct not found.")


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