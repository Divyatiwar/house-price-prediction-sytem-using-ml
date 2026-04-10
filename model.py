import pandas as pd

# STEP 1: Load clean dataset
df = pd.read_csv("clean_housing_data.csv")

print("✅ Dataset Loaded")
print(df.head())

# STEP 2: Remove missing values (just in case)
df = df.dropna()

print("Remaining rows:", len(df))

# STEP 3: Select features & target
X = df[["bhk", "area"]]   # input features
y = df["price"]           # target

# STEP 4: Train-Test Split
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("Training data:", X_train.shape)
print("Testing data:", X_test.shape)

# STEP 5: Train Linear Regression Model
from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(X_train, y_train)

print("✅ Model trained successfully")

# STEP 6: Prediction
y_pred = model.predict(X_test)

# STEP 7: Evaluation
from sklearn.metrics import r2_score, mean_absolute_error

r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

print("R2 Score:", r2)
print("MAE:", mae)

# STEP 8: Test with sample input
sample = pd.DataFrame([[3, 1500]], columns=["bhk", "area"])
predicted_price = model.predict(sample)

print("Predicted Price:", predicted_price[0])

# STEP 9: Save model
import pickle

pickle.dump(model, open("model.pkl", "wb"))
print("✅ Model saved as model.pkl")