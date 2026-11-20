from percentage_discount import PercentageDiscount


class StudentDiscount(PercentageDiscount):
    def __init__(self) -> None:
        super().__init__(5)
