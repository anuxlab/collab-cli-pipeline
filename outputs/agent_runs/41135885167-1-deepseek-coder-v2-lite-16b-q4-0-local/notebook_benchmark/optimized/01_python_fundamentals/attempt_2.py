import statistics

# Define the list
data = [4, 7, 7, 10, 12, 14, 18]

# Calculate count
count = len(data)

# Calculate mean
mean = sum(data) / count

# Calculate median
median = statistics.median(data)

# Calculate population variance
variance = statistics.pvariance(data)

# Calculate min and max
min_val = min(data)
max_val = max(data)

# Print results
print(f"Count: {count}")
print(f"Mean: {mean}")
print(f"Median: {median}")
print(f"Population Variance: {variance}")
print(f"Min: {min_val}")
print(f"Max: {max_val}")

# Assert results
assert count == 7
assert mean == (4 + 7 + 7 + 10 + 12 + 14 + 18) / 7
assert median == 10
assert variance == statistics.pvariance(data)
assert min_val == 4
assert max_val == 18

# Print final line with benchmark result
print(f"BENCHMARK_RESULT={{{'task_id': 123, 'count': {count}, 'mean': {mean}, 'median': {median}, 'variance': {variance}, 'min': {min_val}, 'max': {max_val}}}")
