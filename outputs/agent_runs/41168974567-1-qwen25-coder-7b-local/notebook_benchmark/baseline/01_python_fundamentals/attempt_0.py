import json
import statistics

# Given list
data = [4, 7, 7, 10, 12, 14, 18]

# Calculate count
count = len(data)

# Calculate mean
mean = statistics.mean(data)

# Calculate median
median = statistics.median(data)

# Calculate population variance
variance = statistics.variance(data)

# Calculate min and max
min_val = min(data)
max_val = max(data)

# Assertions to validate results
assert count == 7, f"Expected count to be 7, got {count}"
assert mean == 10.428571428571429, f"Expected mean to be 10.428571428571429, got {mean}"
assert median == 10, f"Expected median to be 10, got {median}"
assert variance == 27.142857142857146, f"Expected variance to be 27.142857142857146, got {variance}"
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
