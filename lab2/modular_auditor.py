failed_entries = 0

def get_valid_input():
    global failed_entries

    while True:
        stock_quantity = input("Enter stock quantity: ")

        if stock_quantity.lower() == "quit":
            return "quit"

        elif stock_quantity[:1] == "-" and stock_quantity[1:].isdigit():
            print("Negative numbers not accepted.")
            failed_entries += 1

        elif not stock_quantity.isdigit():
            print("Enter an integer.")
            failed_entries += 1
            
        else:
            return int(stock_quantity)

def process_delivery(current_total, new_value):
    current_total += new_value
    return current_total