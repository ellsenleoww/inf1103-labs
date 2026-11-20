from product import Product
from order_line import OrderLine


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
