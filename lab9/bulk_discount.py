from math import isfinite
from discount_strategy import DiscountStrategy


class BulkDiscount(DiscountStrategy):
    def __init__(self, threshold: float, amount: float) -> None:
        if not isfinite(threshold) or threshold < 0:
            raise ValueError("Threshold must be a finite non-negative number.")
        if not isfinite(amount) or amount < 0:
            raise ValueError("Discount amount must be a finite non-negative number.")
        self.__threshold = threshold
        self.__amount = amount

    def apply(self, total: float) -> float:
        self.validate_total(total)
        if total >= self.__threshold:
            return round(max(0.0, total - self.__amount), 2)
        return total
