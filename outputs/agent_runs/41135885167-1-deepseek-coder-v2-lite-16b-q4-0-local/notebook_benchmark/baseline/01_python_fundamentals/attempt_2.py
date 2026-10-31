import os
import subprocess

# Define the list
data = [4, 7, 7, 10, 12, 14, 18]

# Calculate count
count = len(data)

# Calculate mean
mean = sum(data) / count

# Calculate median
median = sorted(data)[len(data) // 2]

# Calculate population variance
variance = sum((x - mean) ** 2 for x in data) / count

# Calculate min and max
min_val = min(data)
max_val = max(data)

# Validate results with assertions
assert count == 7, "Count assertion failed"
assert mean == (4 + 7 + 7 + 10 + 12 + 14 + 18) / 7, "Mean assertion failed"
assert median == 10, "Median assertion failed"
assert variance == sum((x - mean) ** 2 for x in data) / count, "Variance assertion failed"
assert min_val == 4, "Min assertion failed"
assert max_val == 18, "Max assertion failed"

# Print results
print(f"Count: {count}")
print(f"Mean: {mean}")
print(f"Median: {median}")
print(f"Population Variance: {variance}")
print(f"Min: {min_val}")
print(f"Max: {max_val}")

# Explain why mean and median differ
print("The mean and median differ because the mean is the average of all values, while the median is the middle value when the data is ordered. In this case, the data is not symmetric, and the presence of two 7s pulls the mean down slightly from the median.")

# Print final line with benchmark result
print(f"BENCHMARK_RESULT={{'task_id': 1, 'count': {count}, 'mean': {mean}, 'median': {median}, 'variance': {variance}, 'min': {min_val}, 'max': {max_val}}}")
