inventory = 0
failed_entries = 0

while True:
    stock_quantity = input("Enter stock quantity: ")

    if stock_quantity.lower() == "quit":
        break