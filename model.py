import pandas as pd
import json
from keras.models import Sequential
from keras.layers import LSTM, Dense
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from script import getDataFrame, getXDaySpecificDF, getXDayStartTimestamp,getXDayEndTimestamp, getWBGTCategory
from datetime import datetime, timedelta


def trainModel(station_id):
    station_id='S50'
    # 1 Model for each station
    df = getDataFrame(station_id)

    # Split the data into input features (X) and target variable (y)
    X = df[['temperature', 'humidity']].values
    y = df['WBGT'].values

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Reshape the input features for LSTM (assuming you have a time step of 1)
    X_train = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])
    X_test = X_test.reshape(X_test.shape[0], 1, X_test.shape[1])

    # Build the LSTM model
    model = Sequential()
    model.add(LSTM(25, input_shape=(X_train.shape[1], X_train.shape[2])))
    model.add(Dense(1))

    # Compile the model
    model.compile(loss='mean_squared_error', optimizer='adam')

    # Train the model
    model.fit(X_train, y_train, epochs=20, batch_size=32, validation_data=(X_test, y_test))

    model_filename = f'model_{station_id}.h5'

    model.save(model_filename)

def predictModel(model,hour,df):
    current_time = datetime.now()
    # Calculate the end point of the 5-hour interval from the current time
    end_time = current_time - timedelta(hours=hour)

    # Filter the DataFrame to get rows within the 5-hour interval (Include the current time as well)
    new_df = df[df['timestamp'] > end_time]

    # Calculate the number of rows to select (approximately 4 per hour)
    num_rows_to_select = 4 * hour
    num_rows = len(new_df)

    # Select rows at regular intervals
    interval = max(1, num_rows // num_rows_to_select)  # Ensure at least 1 row selected
    selected_indices = range(0, num_rows, interval)
    selected_rows = new_df.iloc[selected_indices]

    X = selected_rows[['temperature', 'humidity']].values
    X = X.reshape(X.shape[0], 1, X.shape[1])
    
    # Predict using the model
    predictions = model.predict(X)

    # Create a new DataFrame to store the timestamp and predictions
    timestamp_values = selected_rows['timestamp'].values
    predicted_values = predictions.reshape(-1)
    
    # Create a list to store the timestamp and predictions as dictionaries
    result_list = []
    for timestamp, prediction in zip(selected_rows['timestamp'], predictions):
        # Convert timestamp to string in the desired format (adjust format as needed)

        future_timestamp = timestamp + timedelta(hours=hour)

        timestamp_str = future_timestamp.strftime('%Y-%m-%d %H:%M:%S')

        # Append the timestamp and prediction as dictionaries to the result_list
        result_list.append({'timestamp': timestamp_str, 'predicted_value': str(prediction[0])})

    # Convert the result_list to JSON format
    result_json = json.dumps(result_list)

    return result_json

# For predicting base on a given timestamp: MSE Checking for specific interval within a day

def predictGivenTimestamp(model,givenTimeframe,df):

    # Set the desired hour interval here (e.g., 9 hours)
    hour_interval = 24

    # Calculate the end point of the hour_interval from the given time
    end_time = givenTimeframe - timedelta(hours=hour_interval)

    # Filter the DataFrame to get rows within the hour interval (Include the current time as well)
    new_df = df[(df['timestamp'] > end_time) & (df['timestamp'] <= givenTimeframe)]

    # Calculate the number of rows to select (approximately 4 per hour)
    num_rows_to_select = 4 * hour_interval
    num_rows = len(new_df)

    # Select rows at regular intervals
    interval = max(1, num_rows // num_rows_to_select)  # Ensure at least 1 row selected
    selected_indices = range(0, num_rows, interval)
    selected_rows = new_df.iloc[selected_indices]

    X = selected_rows[['temperature', 'humidity']].values
    X = X.reshape(X.shape[0], 1, X.shape[1])
    
    # Predict using the model
    predictions = model.predict(X)

    # Create a new DataFrame to store the timestamp and predictions
    timestamp_values = selected_rows['timestamp'].values
    predicted_values = predictions.reshape(-1)
    
    # Create a list to store the timestamp and predictions as dictionaries
    result_list = []
    for timestamp, prediction in zip(selected_rows['timestamp'], predictions):
        # Convert timestamp to string in the desired format (adjust format as needed)
        future_timestamp = timestamp + timedelta(hours=hour_interval)
        timestamp_str = future_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        # Append the timestamp and prediction as dictionaries to the result_list
        result_list.append({'timestamp': timestamp_str, 'wbgt': prediction[0]})

    # Convert the result_list to a pandas DataFrame
    result_df = pd.DataFrame(result_list)

    return result_df

def cleanActualData(givenTimeframe, df):

    # Set the desired hour interval here (e.g., 9 hours)
    hour_interval = 24

    # Calculate the end point of the hour_interval from the given time
    end_time = givenTimeframe - timedelta(hours=hour_interval)

    # Filter the DataFrame to get rows within the hour interval (including the current time)
    new_df = df[(df['timestamp'] >= end_time) & (df['timestamp'] <= givenTimeframe)]

    # Calculate the number of rows to select (approximately 4 per hour)
    num_rows_to_select = 4 * hour_interval
    num_rows = len(new_df)

    # Select rows at regular intervals
    interval = max(1, num_rows // num_rows_to_select)  # Ensure at least 1 row selected
    selected_indices = range(0, num_rows, interval)
    selected_rows = new_df.iloc[selected_indices]

    # Create a new DataFrame to store the timestamp and actual WBGT values
    timestamp_values = selected_rows['timestamp'].values
    actual_values = selected_rows['WBGT'].values

    # Create a list to store the timestamp and actual WBGT values as dictionaries
    result_list = []
    for timestamp, actual_wbgt in zip(selected_rows['timestamp'], selected_rows['WBGT']):
        # Convert timestamp to string in the desired format (adjust format as needed)
        future_timestamp = timestamp + timedelta(hours=hour_interval)
        timestamp_str = future_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        # Append the timestamp and actual WBGT as dictionaries to the result_list
        result_list.append({'timestamp': timestamp_str, 'wbgt_actual': actual_wbgt})

    # Convert the result_list to a pandas DataFrame
    result_df = pd.DataFrame(result_list)

    return result_df

# For X Day forecasting

def xDayForecast(model,day,station_id):

    backtracked_time = getXDayStartTimestamp(day)
    end_time = getXDayEndTimestamp(day)
    df = getXDaySpecificDF(station_id,backtracked_time,end_time)

    X = df[['temperature', 'humidity']].values
    X = X.reshape(X.shape[0], 1, X.shape[1])

    # Predict using the model
    predictions = model.predict(X)

    # Create a list to store the timestamp and predictions as dictionaries
    result_list = []
    for timestamp, prediction in zip(df['timestamp'], predictions):
        # Convert timestamp to string in the desired format (adjust format as needed)
        future_timestamp = timestamp + timedelta(days=day)
        timestamp_str = future_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        # Append the timestamp and prediction as dictionaries to the result_list
        result_list.append({'timestamp': timestamp_str, 'wbgt': prediction[0]})

    # Convert the result_list to a pandas DataFrame
    result_df = pd.DataFrame(result_list)

    return result_df

def min_max_day(df):

    # Convert the 'timestamp' column to pandas datetime format
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Extract the date part from the timestamp
    df['date'] = df['timestamp'].dt.date

    # Group the data by date and calculate the minimum and maximum 'wbgt' values for each date
    agg_df = df.groupby('date')['wbgt'].agg(min_wbgt='min', max_wbgt='max').reset_index()

    # Rename the 'date' column to 'timestamp'
    agg_df = agg_df.rename(columns={'date': 'timestamp'})

    print(agg_df)

    # # Create WBGT Category for Min value
    # agg_df['Min_Category'] = df.apply(lambda row: getWBGTCategory(row['min_wbgt']),axis=1)

    # # Create WBGT Category for Min value
    # agg_df['Max_Category'] = df.apply(lambda row: getWBGTCategory(row['max_wbgt']),axis=1)

    return agg_df


def MSE(predicted_data_df,cleanActualData_df ):

    actual_wbgt = cleanActualData_df['wbgt_actual']
    predicted_wbgt = predicted_data_df['wbgt']

    while actual_wbgt.shape[0] > predicted_wbgt.shape[0]:
        # Align it with the same length as the predicted
        actual_wbgt = actual_wbgt.drop(actual_wbgt.index[-1])

    while predicted_wbgt.shape[0] > actual_wbgt.shape[0]:
        predicted_wbgt = predicted_wbgt.drop(predicted_wbgt.index[-1])

    mse = mean_squared_error(actual_wbgt, predicted_wbgt)

    return mse