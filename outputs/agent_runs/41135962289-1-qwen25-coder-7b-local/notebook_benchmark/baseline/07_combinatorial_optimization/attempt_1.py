import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations

# Define the problem
task_id = "01_knapsack"
capacity = 50
items = [
    (10, 60), (20, 100), (30, 120), (40, 140), (50, 160),
    (60, 180), (70, 200), (80, 220), (90, 240), (100, 260),
    (110, 280), (120, 300)
]

# Greedy algorithm
def greedy_knapsack(items, capacity):
    items.sort(key=lambda x: x[1] / x[0], reverse=True)
    selected = []
    total_weight = 0
    total_value = 0
    for item in items:
        if total_weight + item[0] <= capacity:
            selected.append(item)
            total_weight += item[0]
            total_value += item[1]
    return total_value, selected

# Dynamic Programming solution
def dp_knapsack(items, capacity):
    n = len(items)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(1, capacity + 1):
            if items[i-1][0] <= w:
                dp[i][w] = max(dp[i-1][w], dp[i-1][w-items[i-1][0]] + items[i-1][1])
            else:
                dp[i][w] = dp[i-1][w]
    return dp[n][capacity]

# Brute-force solution for small instances
def brute_force_knapsack(items, capacity):
    max_value = 0
    best_combination = []
    for r in range(1, len(items) + 1):
        for combination in combinations(items, r):
            total_weight = sum(item[0] for item in combination)
            total_value = sum(item[1] for item in combination)
            if total_weight <= capacity and total_value > max_value:
                max_value = total_value
                best_combination = combination
    return max_value, best_combination

# Execute algorithms
greedy_value, greedy_selected = greedy_knapsack(items, capacity)
optimal_value = dp_knapsack(items, capacity)
optimal_weight = sum(item[0] for item in greedy_selected)
item_count = len(items)

# Brute-force cross-check for small instances
if len(items) <= 10:
    brute_force_value, brute_force_selected = brute_force_knapsack(items, capacity)
    assert optimal_value == brute_force_value, "Optimal value does not match brute-force result"

# Plot value/weight
weights = [item[0] for item in items]
values = [item[1] for item in items]
plt.figure(figsize=(10, 5))
plt.scatter(weights, values, color='blue')
plt.xlabel('Weight')
plt.ylabel('Value')
plt.title('Item Value vs Weight')
plt.show()

# Print results
BENCHMARK_RESULT = {
    "task_id": task_id,
    "capacity": capacity,
    "greedy_value": greedy_value,
    "optimal_value": optimal_value,
    "optimal_weight": optimal_weight,
    "item_count": item_count
}
print(BENCHMARK_RESULT)
