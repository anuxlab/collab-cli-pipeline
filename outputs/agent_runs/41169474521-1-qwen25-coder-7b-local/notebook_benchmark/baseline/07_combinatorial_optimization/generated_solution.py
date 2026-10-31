import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations

# Set random seed for reproducibility
np.random.seed(42)

# Generate a random 0/1 knapsack problem
item_count = 12
capacity = 30
weights = np.random.randint(1, 10, item_count)
values = np.random.randint(1, 10, item_count)

# Plot value vs weight
plt.figure(figsize=(10, 5))
plt.bar(range(item_count), weights, label='Weight')
plt.bar(range(item_count), values, bottom=weights, label='Value')
plt.xlabel('Item')
plt.ylabel('Value/Weight')
plt.title('Knapsack Items')
plt.legend()
plt.show()

# Greedy value/weight heuristic
def greedy_knapsack(weights, values, capacity):
    items = list(range(len(weights)))
    items.sort(key=lambda i: values[i] / weights[i], reverse=True)
    selected = []
    total_weight = 0
    total_value = 0
    for item in items:
        if total_weight + weights[item] <= capacity:
            selected.append(item)
            total_weight += weights[item]
            total_value += values[item]
    return total_value, selected

greedy_value, greedy_selected = greedy_knapsack(weights, values, capacity)
print(f'Greedy Value: {greedy_value}')

# Exact method using dynamic programming
def dynamic_knapsack(weights, values, capacity):
    n = len(weights)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(1, capacity + 1):
            if weights[i - 1] <= w:
                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - weights[i - 1]] + values[i - 1])
            else:
                dp[i][w] = dp[i - 1][w]
    return dp[n][capacity]

optimal_value = dynamic_knapsack(weights, values, capacity)
print(f'Optimal Value: {optimal_value}')

# Brute-force cross-check for a small instance
def brute_force_knapsack(weights, values, capacity):
    n = len(weights)
    max_value = 0
    best_combination = []
    for r in range(1, n + 1):
        for comb in combinations(range(n), r):
            comb_weight = sum(weights[i] for i in comb)
            comb_value = sum(values[i] for i in comb)
            if comb_weight <= capacity and comb_value > max_value:
                max_value = comb_value
                best_combination = comb
    return max_value, best_combination

optimal_value_brute, optimal_combination = brute_force_knapsack(weights, values, capacity)
print(f'Brute-Force Value: {optimal_value_brute}')
print(f'Brute-Force Selected: {optimal_combination}')

# Verify feasibility
optimal_weight = sum(weights[i] for i in optimal_combination)
print(f'Optimal Weight: {optimal_weight}')
print(f'Optimal Feasibility: {optimal_weight <= capacity}')

# Print the benchmark result
BENCHMARK_RESULT = {
    "task_id": "01_knapsack",
    "capacity": capacity,
    "greedy_value": greedy_value,
    "optimal_value": optimal_value,
    "optimal_weight": optimal_weight,
    "item_count": item_count
}
print(BENCHMARK_RESULT)
