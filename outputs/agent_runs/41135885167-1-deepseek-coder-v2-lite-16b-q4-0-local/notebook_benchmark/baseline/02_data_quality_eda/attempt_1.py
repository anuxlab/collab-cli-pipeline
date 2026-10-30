import pandas as pd
import matplotlib.pyplot as plt

# Construct DataFrame
data = {
    'date': ['2022-01-01', '2022-02-01', '2022-03-01', '2022-04-01', '2022-05-01', '2022-06-01', '2022-07-01', '2022-08-01', '2022-09-01', '2022-10-01', '2022-11-01', '2022-12-01'],
    'region': ['East', 'West', 'North', 'South', 'East', 'West', 'North', 'South', 'East', 'West', 'North', 'South'],
    'product': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
    'units': [100, 200, 150, 250, 120, 180, 130, 220, 110, 210, 140, 230],
    'unit_price': [10, 15, 12, 18, 11, 16, 13, 19, 10, 17, 12, 19],
    'customer_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
}

df = pd.DataFrame(data)

# Introduce missing value and a duplicate
df.loc[5, 'units'] = None  # Introduce missing value
df = df.append(df.iloc
