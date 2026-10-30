import json

# Given list
data = [4, 7, 7, 10, 12, 14, 18]

# Calculate count
count = len(data)

# Calculate mean
mean = sum(data) / count

# Calculate median
sorted_data = sorted(data)
n = len(sorted_data)
if n % 2 == 1:
    median = sorted_data[n // 2]
else:
    median = (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2

# Calculate population variance
variance = sum((x - mean) ** 2 for x in data) / count

# Calculate min and max
min_val = min(data)
max_val = max(data)

# Assertions for validation
assert count == 7, f"Expected count to be 7, got {count}"
assert mean == 10.571428571428571, f"Expected mean to be 10.571428571428571, got {mean}"
assert median == 10, f"Expected median to be 10, got {median}"
assert variance == 26.428571428571427, f"Expected variance to be 26.428571428571427, got {variance}"
assert min_val == 4, f"Expected min to be 4, got {min_val}"
assert max_val == 18, f"Expected max to be 18, got {max_val}"

# Print final result
BENCHMARK_RESULT = json.dumps({
    "task_id": "task_1",
    "count": count,
    "mean": mean,
    "median": median,
    "variance": variance,
    "min": min_val,
    "max": max_val
})
print(BENCHMARK_RESULT)
