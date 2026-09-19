inventory = 0
failed_entries = 0

while True:
    stock_quantity = input("Enter stock quantity: ")

    if stock_quantity.lower() == "quit":
        break

    elif stock_quantity[:1] == "-" and stock_quantity[1:].isdigit():
        print("Negative numbers not accepted.")
        failed_entries += 1
    
    elif not stock_quantity.isdigit():
        print("Enter an integer.")
        failed_entries += 1

    else:
        inventory += int(stock_quantity)

        if inventory > 500:
            print("Exceeded 500.")
            break

print("Total Units Processed:", inventory)
print("Number of Failed/Rejected Entries:", failed_entries)