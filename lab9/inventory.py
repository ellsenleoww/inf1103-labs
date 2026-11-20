from product import Product


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
