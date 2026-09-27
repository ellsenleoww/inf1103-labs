failed_entries = 0

def load_inventory():
    try:
        with open("inventory.txt", "r") as file:
            total_line = file.readline().strip()
            history_line = file.readline().strip()

            if total_line == "":
                total = 0
            else:
                total = int(total_line)

            history = []

            if history_line != "":
                values = history_line.split(",")

                for value in values:
                    history.append(int(value))

            return total, history

    except FileNotFoundError:
        return 0, []

def save_inventory(total_units, transaction_history):
    with open("inventory.txt", "w") as file:
        file.write(str(total_units) + "\n")

        for i in range(len(transaction_history)):
            file.write(str(transaction_history[i]))

            if i < len(transaction_history) - 1:
                file.write(",")

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

def calculate_tax(amount):
    tax = amount * 0.10
    return tax

def generate_report(total_units, failed_attempts):
    print("Total Units Processed:", total_units)
    print("Number of Failed/Rejected Entries:", failed_attempts)

# Load previous inventory
inventory, transaction_history = load_inventory()

while True:
    stock_quantity = get_valid_input()

    if stock_quantity == "quit":
        break

    # Update total inventory
    inventory = process_delivery(inventory, stock_quantity)

    # Store transaction
    transaction_history.append(stock_quantity)

    # Calculate tax
    tax = calculate_tax(stock_quantity)
    print("Tax for this delivery:", tax)

# Save everything when user quits
save_inventory(inventory, transaction_history)

generate_report(inventory, failed_entries)

print("Inventory successfully saved to inventory.txt")