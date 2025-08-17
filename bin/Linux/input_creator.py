import math

# Prompt the user to enter the formula
formula = input("Enter the formula (use 't' as the variable): ")

# Define the time step and the total time
time_step = 0.001
total_time = 10

# Calculate the number of steps
num_steps = int(total_time / time_step) + 1

# Open the file in write mode
with open('input.txt', 'w') as file:
    # Loop to generate values for t from 0 to total_time
    for step in range(num_steps):
        t = step * time_step
        # Calculate the value of the formula using eval
        y = eval(formula)
        # Write the value to the file in scientific notation
        file.write(f"{y}\n")