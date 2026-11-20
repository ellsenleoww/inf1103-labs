from dataclasses import dataclass
from product import Product


@dataclass(frozen=True)
class OrderLine:
    product: Product
    quantity: int

    def __post_init__(self) -> None:
        if type(self.quantity) is not int or self.quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

    def calculate_subtotal(self) -> float:
        return self.product.price * self.quantity
