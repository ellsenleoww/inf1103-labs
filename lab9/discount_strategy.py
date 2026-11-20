from abc import ABC, abstractmethod
from math import isfinite


class DiscountStrategy(ABC):
    @abstractmethod
    def apply(self, total: float) -> float:
        pass

    @staticmethod
    def validate_total(total: float) -> None:
        if not isfinite(total) or total < 0:
            raise ValueError("Total must be a finite non-negative number.")
