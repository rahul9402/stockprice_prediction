
import streamlit as st

# Your existing code here...
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.metrics import BinaryAccuracy




def extract_additional_features(data):
    # Example: Suppose you're predicting the next day's trend based on today's closing price
    data['Next_Day_Trend'] = np.where(data['Close'].shift(-1) > data['Close'], 1, 0)
    return data




st.title('Stock Prediction App')

# Sidebar for user input
st.sidebar.header('User Input')

# User inputs for stock symbol, start date, and end date
ticker_symbol = st.sidebar.text_input('Stock Symbol', 'GAIL.NS')
start_date = st.sidebar.text_input('Start Date', '2022-03-01')
end_date = st.sidebar.text_input('End Date', '2022-12-13')

# Fetch historical data from Yahoo Finance
stock_data = yf.download(ticker_symbol, start=start_date, end=end_date)

# Display the retrieved historical stock data
st.subheader('Raw Historical Stock Data:')
st.dataframe(stock_data.head())

def extract_additional_features(data):
    # Example: Suppose you're predicting the next day's trend based on today's closing price
    data['Next_Day_Trend'] = np.where(data['Close'].shift(-1) > data['Close'], 1, 0)
    return data


# Preprocessing and Feature Engineering
clean_stock_data = stock_data.fillna(method='ffill')  # Forward-fill missing values

# Calculate Moving Averages
clean_stock_data['Short_MA'] = clean_stock_data['Close'].rolling(window=10).mean()
clean_stock_data['Long_MA'] = clean_stock_data['Close'].rolling(window=50).mean()

# Calculate Relative Strength Index (RSI)
delta = clean_stock_data['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=50).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=50).mean()
RS = gain / loss
RSI = 100 - (100 / (1 + RS))
clean_stock_data['RSI'] = RSI

# Drop NaN values generated by rolling calculations
clean_stock_data.dropna(inplace=True)

# Extract additional features
clean_stock_data = extract_additional_features(clean_stock_data)

# Algorithm Implementation and Training
features = ['Short_MA', 'Long_MA', 'RSI', 'Next_Day_Trend']
target = 'Close'

train_size = int(0.8 * len(clean_stock_data))
train_data = clean_stock_data[:train_size]
test_data = clean_stock_data[train_size:]



# Training using Linear Regression as a baseline model
model_lr = LinearRegression()
model_lr.fit(train_data[features], train_data[target])

# Training using Support Vector Machine (SVR)
model_svr = SVR(kernel='linear')
model_svr.fit(train_data[features], train_data[target])

# Training using Random Forest
model_rf = RandomForestRegressor(n_estimators=100, random_state=42)
model_rf.fit(train_data[features], train_data[target])

# Training using Gradient Boosting
model_gb = GradientBoostingRegressor(n_estimators=100, random_state=42)
model_gb.fit(train_data[features], train_data[target])

# LSTM model
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(clean_stock_data[features + [target]])
X = []
y = []
for i in range(50, len(scaled_data)):
    X.append(scaled_data[i-50:i, :-1])
    y.append(scaled_data[i, -1])

X, y = np.array(X), np.array(y)
X = np.reshape(X, (X.shape[0], X.shape[1], len(features)))

model_lstm = Sequential()
model_lstm.add(LSTM(units=50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])))
model_lstm.add(LSTM(units=50, return_sequences=False))
model_lstm.add(Dense(units=1))
model_lstm.compile(optimizer='adam', loss='mean_squared_error')
model_lstm.fit(X, y, epochs=50, batch_size=32)

# Evaluation
def evaluate_model(model, test_features, test_target):
    predictions = model.predict(test_features)
    mse = mean_squared_error(test_target, predictions)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(test_target, predictions)
    r2 = r2_score(test_target, predictions)
    return mse, rmse, mae, r2

# Evaluate Linear Regression model
mse_lr, rmse_lr, mae_lr, r2_lr = evaluate_model(model_lr, test_data[features], test_data[target])
print("Linear Regression:")
print(f"MSE: {mse_lr}, RMSE: {rmse_lr}, MAE: {mae_lr}, R-squared: {r2_lr}")

# Evaluate SVR model
mse_svr, rmse_svr, mae_svr, r2_svr = evaluate_model(model_svr, test_data[features], test_data[target])
print("Support Vector Machine (SVR):")
print(f"MSE: {mse_svr}, RMSE: {rmse_svr}, MAE: {mae_svr}, R-squared: {r2_svr}")

# Evaluate Random Forest model
mse_rf, rmse_rf, mae_rf, r2_rf = evaluate_model(model_rf, test_data[features], test_data[target])
print("Random Forest:")
print(f"MSE: {mse_rf}, RMSE: {rmse_rf}, MAE: {mae_rf}, R-squared: {r2_rf}")

# Evaluate Gradient Boosting model
mse_gb, rmse_gb, mae_gb, r2_gb = evaluate_model(model_gb, test_data[features], test_data[target])
print("Gradient Boosting:")
print(f"MSE: {mse_gb}, RMSE: {rmse_gb}, MAE: {mae_gb}, R-squared: {r2_gb}")

# Evaluate LSTM model
test_data_lstm = scaled_data[train_size-50:, :-1]
X_test_lstm = []
for i in range(50, len(test_data_lstm)):
    X_test_lstm.append(test_data_lstm[i-50:i, :])

X_test_lstm = np.array(X_test_lstm)
X_test_lstm = np.reshape(X_test_lstm, (X_test_lstm.shape[0], X_test_lstm.shape[1], len(features)))

predictions_lstm = model_lstm.predict(X_test_lstm)
predictions_lstm = scaler.inverse_transform(np.concatenate((test_data_lstm[50:, :], predictions_lstm), axis=1))[:, -1]

mse_lstm = mean_squared_error(clean_stock_data['Close'].values[train_size:], predictions_lstm)
print("LSTM:")
print(f"MSE: {mse_lstm}")

model_mse = {
    'Linear Regression': mse_lr,
    'SVR': mse_svr,
    'Random Forest': mse_rf,
    'Gradient Boosting': mse_gb,
    'LSTM': mse_lstm
}

# Find the model with the lowest MSE
best_model = min(model_mse, key=model_mse.get)
lowest_mse = model_mse[best_model]

# Streamlit components for model evaluation and predictions
st.subheader('Model Evaluation and Prediction')

# Display MSE values for all models
for model, mse in model_mse.items():
    st.write(f"{model} MSE: {mse}")

# Display the best model with the lowest MSE
st.write(f"\nThe best model with the lowest MSE is {best_model} with MSE: {lowest_mse}")

# Assuming LSTM model is the best-performing model

# Streamlit components for future predictions
future_days = 1  # Replace with the desired number of future days

last_short_ma = clean_stock_data['Short_MA'].iloc[-1]
last_long_ma = clean_stock_data['Long_MA'].iloc[-1]
last_rsi = clean_stock_data['RSI'].iloc[-1]
last_trend = clean_stock_data['Next_Day_Trend'].iloc[-1]

future_short_ma_values = []  # Store future Short_MA values
future_long_ma_values = []  # Store future Long_MA values
future_rsi_values = []  # Store future RSI values
future_trend_values = []  # Store future Next_Day_Trend values

for i in range(future_days):
    # Example: Suppose you're predicting the next day's trend based on today's values
    # Replace this with your own forecasting logic
    future_short_ma_values.append(last_short_ma + 1)  # Placeholder logic
    future_long_ma_values.append(last_long_ma + 1)  # Placeholder logic
    future_rsi_values.append(last_rsi + 1)  # Placeholder logic
    future_trend_values.append(last_trend + 1)  # Placeholder logic

# Display future features
future_features = pd.DataFrame({
    'Short_MA': future_short_ma_values,
    'Long_MA': future_long_ma_values,
    'RSI': future_rsi_values,
    'Next_Day_Trend': future_trend_values
})

st.subheader('Using Technical Indicators :')
st.dataframe(future_features)

# Predict open prices for the next 'n' days using the selected model (e.g., Linear Regression)
predicted_open_prices = model_lr.predict(future_features)
st.subheader('Predicted Future Open Prices:')
st.write(predicted_open_prices)
