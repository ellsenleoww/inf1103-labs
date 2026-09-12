inventory = 0

while True:
    stock_quantity = input("Enter stock quantity: ")

    if stock_quantity.lower() == "quit":
        break
    
    elif not stock_quantity.isdigit():
        print("Enter an integer.")