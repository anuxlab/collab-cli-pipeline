import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations

# Set random seed for reproducibility
np.random.seed(42)

# Define the problem parameters
capacity = 50
item_count = 12

# Generate random weights and values for the items
weights = np.random.randint(1, 10, item_count)
values = np.random.randint(1, 10, item_count)

# Create a dictionary to store item details
items = {i: {'weight': weights[i], 'value': values[i]} for i in range(item_count)}

# Plot the value/weight ratio for each item
plt.figure(figsize=(10, 5))
plt.bar(range(item_count), values / weights, tick_label=range(1, item_count + 1))
plt.xlabel('Item')
plt.ylabel('Value/Weight Ratio')
plt.title('Value/Weight Ratio of Items')
plt.show()

# Greedy algorithm based on value/weight ratio
def greedy_knapsack(items, capacity):
    items_sorted = sorted(items.items(), key=lambda x: x[1]['value'] / x[1]['weight'], reverse=True)
    selected_items = []
    total_weight = 0
    total_value = 0
    for item, details in items_sorted:
        if total_weight + details['weight'] <= capacity:
            selected_items.append(item)
            total_weight += details['weight']
            total_value += details['value']
    return selected_items, total_value, total_weight

# Exact method using dynamic programming
def dynamic_knapsack(items, capacity):
    n = len(items)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(1, capacity + 1):
            if items[i-1]['weight'] <= w:
                dp[i][w] = max(dp[i-1][w], dp[i-1][w-items[i-1]['weight']] + items[i-1]['value'])
            else:
                dp[i][w] = dp[i-1][w]
    selected_items = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected_items.append(i-1)
            w -= items[i-1]['weight']
    return selected_items, dp[n][capacity]

# Brute-force method for small instances
def brute_force_knapsack(items, capacity):
    n = len(items)
    max_value = 0
    best_combination = []
    for r in range(1, n + 1):
        for combination in combinations(items.keys(), r):
            total_weight = sum(items[item]['weight'] for item in combination)
            total_value = sum(items[item]['value'] for item in combination)
            if total_weight <= capacity and total_value > max_value:
                max_value = total_value
                best_combination = combination
    return list(best_combination), max_value, sum(items[item]['weight'] for item in best_combination)

# Run the algorithms
greedy_items, greedy_value, greedy_weight = greedy_knapsack(items, capacity)
dp_items, optimal_value, optimal_weight = dynamic_knapsack(items, capacity)
if item_count <= 10:  # Only run brute-force for small instances
    brute_force_items, brute_force_value, brute_force_weight = brute_force_knapsack(items, capacity)
    assert optimal_value == brute_force_value, "Optimal value does not match brute-force result"

# Print the results
print(f"Greedy Value: {greedy_value}")
print(f"Optimal Value: {optimal_value}")
print(f"Optimal Weight: {optimal_weight}")
print(f"Selected Items (Greedy): {greedy_items}")
print(f"Selected Items (DP): {dp_items}")
if item_count <= 10:
    print(f"Selected Items (Brute-Force): {brute_force_items}")

# Benchmark result
BENCHMARK_RESULT = {
    "task_id": "01_knapsack",
    "capacity": capacity,
    "greedy_value": greedy_value,
    "optimal_value": optimal_value,
    "optimal_weight": optimal_weight,
    "item_count": item_count
}
print(BENCHMARK_RESULT)
