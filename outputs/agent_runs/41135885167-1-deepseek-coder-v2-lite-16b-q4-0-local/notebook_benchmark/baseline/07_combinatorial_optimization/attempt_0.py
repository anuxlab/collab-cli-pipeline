import numpy as np
import matplotlib.pyplot as plt

# Define the problem
items = [
    (2, 3), (1, 2), (3, 4), (2, 2), (1, 1),
    (4, 5), (3, 3), (5, 6), (2, 2), (1, 1),
    (3, 3), (2, 2)
]
capacity = 10

# Unpack items
weights, values = zip(*items)
item_count = len(items)

# Greedy heuristic: sort items by value/weight ratio
ratios = [v / w for v, w in items]
sorted_indices = np.argsort(ratios)[::-1]

# Select items by greedy heuristic
greedy_selected = [0] * item_count
greedy_value = 0
greedy_weight = 0
for i in sorted_indices:
    if greedy_weight + weights[i] <= capacity:
        greedy_selected[i] = 1
        greedy_value += values[i]
        greedy_weight += weights[i]

# Dynamic programming for exact solution
def dynamic_programming_knapsack(values, weights, capacity):
    n = len(values)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    keep = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]

    for i in range(1, n + 1):
        for w in range(1, capacity + 1):
            if weights[i - 1] <= w:
                if values[i - 1] + dp[i - 1][w - weights[i - 1]] > dp[i - 1][w]:
                    dp[i][w] = values[i - 1] + dp[i - 1][w - weights[i - 1]]
                    keep[i][w] = 1
                else:
                    dp[i][w] = dp[i - 1][w]
            else:
                dp[i][w] = dp[i - 1][w]

    # Reconstruct the solution
    selected = [0] * n
    w = capacity
    for i in range(n, 0, -1):
        if keep[i][w]:
            selected[i - 1] = 1
            w -= weights[i - 1]

    optimal_value = dp[n][capacity]
    optimal_weight = sum([weights[i] * selected[i] for i in range(n)])
    return selected, optimal_value, optimal_weight

# Exact method using dynamic programming
optimal_selected, optimal_value, optimal_weight = dynamic_programming_knapsack(values, weights, capacity)

# Brute-force cross-check for a small instance
def brute_force_knapsack(values, weights, capacity):
    n = len(values)
    best_value = 0
    best_combination = None
    for i in range(2**n):
        combination = [(i >> j) & 1 for j in range(n)]
        total_value = sum([values[j] * combination[j] for j in range(n)])
        total_weight = sum([weights[j] * combination[j] for j in range(n)])
        if total_weight <= capacity and total_value > best_value:
            best_value = total_value
            best_combination = combination
    return best_value, best_combination

# Brute-force cross-check
brute_force_value, brute_force_combination = brute_force_knapsack(values, weights, capacity)

# Plot value/weight ratio
plt.figure(figsize=(10, 6))
plt.bar([i for i in range(item_count)], ratios)
plt.xlabel('Item Index')
plt.ylabel('Value/Weight Ratio')
plt.title('Value/Weight Ratio of Items')
plt.show()

# Print results
print("Greedy Selected Items:", greedy_selected)
print("Greedy Value:", greedy_value)
print("Optimal Selected Items:", optimal_selected)
print("Optimal Value:", optimal_value)
print("Optimal Weight:", optimal_weight)
print("Brute-force Optimal Value:", brute_force_value)

# Benchmark result
benchmark_result = {
    "task_id": "knapsack",
    "capacity": capacity,
    "greedy_value": greedy_value,
    "optimal_value": optimal_value,
    "optimal_weight": optimal_weight,
    "item_count": item_count
}
print(benchmark_result)
