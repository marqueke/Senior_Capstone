def loop_until_ten():
    a = 0  # Initialize a to 0

    while True:
        print(f"a is currently: {a}")  # Print the current value of a
        if a == 10:  # Check if a equals 10
            print("a has reached 10, exiting the function.")
            return 1  # Return the value of a and exit the function
        a += 1  # Increment a by 1

# Call the function
result = loop_until_ten()
print(f"The function returned: {result}")
