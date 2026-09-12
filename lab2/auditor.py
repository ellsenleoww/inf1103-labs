inventory = 0

while True:
    stock_quantity = input("Enter stock quantity: ")

    if stock_quantity.lower() == "quit":
        break

    elif stock_quantity[:1] == "-" and stock_quantity[1:].isdigit():
        print("Negative numbers not accepted.")
    
    elif not stock_quantity.isdigit():
        print("Enter an integer.")

    else:
        inventory += int(stock_quantity)

        if inventory > 500:
            print("Exceeded 500.")
            break