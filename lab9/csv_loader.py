import csv
from inventory import Inventory
from product_factory import ProductFactory
from supplier import Supplier


def load_products(path: str, inventory: Inventory, supplier: Supplier) -> None:
    try:
        file = open(path, newline="", encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"Products file not found: {path}")
    except OSError as error:
        print(f"Could not open products file: {error}")
    else:
        loaded = 0
        with file:
            reader = csv.reader(file)
            try:
                header = next(reader, None)
                if header != ["product_type", "product_id", "name", "price", "stock_quantity"]:
                    print("Invalid products CSV header.")
                    return
                for row_number, row in enumerate(reader, start=2):
                    try:
                        product_type, product_id, name, price, stock = row
                        product = ProductFactory.create(
                            product_type, product_id, name, float(price), int(stock), supplier
                        )
                        if not inventory.add_product(product):
                            raise ValueError(f"Product ID already exists: {product_id}")
                    except ValueError as error:
                        print(f"Row {row_number} skipped: {error}")
                    else:
                        loaded += 1
            except (csv.Error, UnicodeError, OSError) as error:
                print(f"Could not finish reading products: {error}")
        print(f"{loaded} products loaded.")
    finally:
        print("Load attempt finished.")
