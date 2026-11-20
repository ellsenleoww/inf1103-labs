from dataclasses import dataclass
from product import Product


@dataclass(frozen=True)
class OrderLine:
    product: Product
    quantity: int

    def calculate_subtotal(self) -> float:
        return self.product.price * self.quantity
