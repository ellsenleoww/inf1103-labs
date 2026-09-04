print("===========")
print("Welcome here")
print("Hello")
print("===========")

username = input("Enter Username: ")
age = int(input("Enter age "))
category = input("Enter Content Category: ")

print("\nInstagram Profile")
print("===========")
print("Username:", username)
print("Age:", age)
print("Category:", category)

if age>40 and category == "fun":
    print("You are old what is fun for you")


bio = "Fun Blogger"
followers = 100

followers += 50
print("Day 1:", followers)

followers += 20
print("Day 2:", followers)

followers -= 10
print("Day 3:", followers)

print("Username:", username)
print("Bio:", bio)
print("Follower", followers)