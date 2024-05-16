import pandas as pd

# Read the CSV file into a DataFrame
df = pd.read_csv('C:/Users/young/PycharmProjects/HousingPredictions/housing/data/cleaned_properties.csv')

# Adjust display options to show all columns without truncation
pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.width', None)  # Set display width to show full content of each column

# Display the head (first few rows) of the DataFrame
print("Head of DataFrame:")
print(df.head())

# Display the last row of the DataFrame
print("\nLast row of DataFrame:")
print(df.tail(1))