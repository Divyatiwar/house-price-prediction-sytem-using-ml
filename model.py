import pandas as pd
import re

df = pd.read_csv("housing_data.csv")

print(df.head())
print(df.info())
def clean_price(price):
    try:
        price = str(price)

        # Remove ₹ and split by newline
        price = price.replace("₹", "").split("\n")[1].strip()

        if "Lac" in price:
            return float(price.replace("Lac", "").strip()) * 100000
        elif "Cr" in price:
            return float(price.replace("Cr", "").strip()) * 10000000
        else:
            return None
    except:
        return None

df["price"] = df["price"].apply(clean_price)

print(df[["price"]].head())

def extract_bhk(title):
    match = re.search(r'(\d+)\s*BHK', str(title))
    return int(match.group(1)) if match else None

df["bhk"] = df["title"].apply(extract_bhk)

print(df[["title", "bhk"]].head())

def extract_area(area):
    match = re.search(r'(\d+)', str(area))
    return int(match.group(1)) if match else None

df["area"] = df["area_info"].apply(extract_area)

print(df[["area_info", "area"]].head())

df = df.dropna()
#Remove Missing Values
print("Remaining rows:", len(df))
print(df.head())

# data for ML

X = df[["bhk", "area"]]   # features (input)
y = df["price"]           # target (output)

print(X.head())
print(y.head())

from sklearn.model_selection import train_test_split

# Split data (80% train, 20% test)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("Training data:", X_train.shape)
print("Testing data:", X_test.shape)

#regression model
from sklearn.linear_model import LinearRegression

# Create model
model = LinearRegression()

# Train model
model.fit(X_train, y_train)

print("✅ Model trained successfully")

# Predict on test data
y_pred = model.predict(X_test)

print("Predictions:", y_pred[:5])

#evalute model
from sklearn.metrics import r2_score, mean_absolute_error

# Evaluation
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

print("R2 Score:", r2)
print("MAE:", mae)

# Test with manual input
sample = pd.DataFrame([[3, 1500]], columns=["bhk", "area"])
predicted_price = model.predict(sample)
print("Predicted Price:", predicted_price[0])