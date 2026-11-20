from math import isfinite
from discount_strategy import DiscountStrategy


class PercentageDiscount(DiscountStrategy):
    def __init__(self, percentage: float) -> None:
        if not isfinite(percentage) or not 0 <= percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100.")
        self.__percentage = percentage

    def apply(self, total: float) -> float:
        self.validate_total(total)
        return round(total * (1 - self.__percentage / 100), 2)
