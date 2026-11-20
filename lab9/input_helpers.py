from math import isfinite


def get_positive_float(prompt: str) -> float:
    while True:
        try:
            value = float(input(prompt))
            if not isfinite(value) or value <= 0:
                print("Please enter a number greater than zero.")
                continue
            return value
        except ValueError:
            print("Please enter a valid number, e.g. 12.50")


def get_nonnegative_float(prompt: str) -> float:
    while True:
        try:
            value = float(input(prompt))
            if not isfinite(value) or value < 0:
                raise ValueError
            return value
        except ValueError:
            print("Please enter a finite number of zero or more.")


def get_integer(prompt: str, minimum: int = 0) -> int:
    while True:
        try:
            value = int(input(prompt))
            if value < minimum:
                raise ValueError
            return value
        except ValueError:
            print(f"Please enter a whole number of {minimum} or more.")
