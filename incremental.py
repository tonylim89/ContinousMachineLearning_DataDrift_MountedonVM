import copy
import pandas as pd
from datetime import timedelta,datetime
from script import sql_connection, sqlCursorDFCode
from keras.models import load_model
from sklearn.metrics import mean_squared_error
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping



# This takes all available data that was stored in our cron job from the current Monday (Maintenance endpoint)

def getNewData():
    
    enddate = datetime.now().strftime("%Y-%m-%d 01:00:00")
    enddate_converted = datetime.strptime(enddate, "%Y-%m-%d %H:%M:%S")

    startdate = enddate_converted - timedelta(days=7)

    connection = sql_connection()
    cursor = connection.cursor()

    query = f"SELECT * FROM temperature_data WHERE station_id = 'S50' AND timestamp >= '{startdate}' AND timestamp <= '{enddate}'"

    new_df = sqlCursorDFCode(cursor,query,connection)
    new_df.drop(columns=['id'],inplace=True)

    columns_to_check = ['timestamp']

    # Drop duplicate timestamp entries
    new_df.drop_duplicates(subset=columns_to_check)

    # Remove if you do not need to see the structure
    print(new_df.head())
    print(new_df.tail())

    return new_df


def getOldData():

    enddate = datetime.now().strftime("%Y-%m-%d 01:00:00")
    enddate_converted = datetime.strptime(enddate, "%Y-%m-%d %H:%M:%S")

    startdate = enddate_converted - timedelta(days=14)

    
    enddate = enddate_converted - timedelta(days=7)

    connection = sql_connection()
    cursor = connection.cursor()

    query = f"SELECT * FROM temperature_data WHERE station_id = 'S50' AND timestamp >= '{startdate}' AND timestamp <= '{enddate}'"

    new_df = sqlCursorDFCode(cursor,query,connection)
    new_df.drop(columns=['id'],inplace=True)

    columns_to_check = ['timestamp']

    # Drop duplicate timestamp entries
    new_df.drop_duplicates(subset=columns_to_check)

    # Remove if you do not need to see the structure
    print(new_df.head())
    print(new_df.tail())

    return new_df


def getRetrainData():

    enddate = datetime.now().strftime("%Y-%m-%d 01:00:00")
    enddate_converted = datetime.strptime(enddate, "%Y-%m-%d %H:%M:%S")
    enddate_converted = enddate_converted - timedelta(days=7)
    startdate = enddate_converted - timedelta(days=37)

    connection = sql_connection()
    cursor = connection.cursor()

    query = f"SELECT * FROM temperature_data WHERE station_id = 'S50' AND timestamp >= '{startdate}' AND timestamp <= '{enddate}'"

    new_df = sqlCursorDFCode(cursor,query,connection)
    new_df.drop(columns=['id'],inplace=True)

    columns_to_check = ['timestamp']

    # Drop duplicate timestamp entries
    new_df.drop_duplicates(subset=columns_to_check)

    # Remove if you do not need to see the structure
    print(new_df.head())
    print(new_df.tail())

    return new_df


def build_model(num_units, input_shape):
    model = Sequential()
    model.add(LSTM(num_units, input_shape=input_shape))
    model.add(Dense(1))
    optimizer = Adam(learning_rate=0.001)
    model.compile(loss='mean_squared_error', optimizer=optimizer)
    return model


# Function to train the model
def train_model(model, X_train, y_train, X_val, y_val, epochs, batch_size):
    early_stopping = EarlyStopping(monitor='val_loss', patience=7, restore_best_weights=True)
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_val, y_val), callbacks=[early_stopping])


def retrain(model):
    
    num_epochs = np.random.choice([50, 100, 150])
    batch_size = 32

    new_data = getRetrainData()

    # Train the model using the new data
    X = new_data[['temperature','humidity']].values
    y = new_data['WBGT'].values
    
    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Reshape the input features for LSTM (assuming you have a time step of 1)
    X_train = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])
    X_test = X_test.reshape(X_test.shape[0], 1, X_test.shape[1])
    num_units = np.random.choice([32, 64, 128])
    input_shape = (X_train.shape[1], X_train.shape[2])

    # Build the model
    model = build_model(num_units, input_shape)

    # Train the model
    train_model(model, X_train, y_train, X_test, y_test, epochs=num_epochs, batch_size=32)
    return model

def compareMSE(model, new_model, X, y):
    X= X.reshape(X.shape[0], 1, X.shape[1])
    predicted_wbgt = model.predict(X)
    actual_wbgt = y
    mse = mean_squared_error(actual_wbgt, predicted_wbgt)
    new_model.fit(X, y, epochs=20, batch_size=32)
    predicted_wbgt = new_model.predict(X)
    actual_wbgt = y
    mse2 = mean_squared_error(actual_wbgt, predicted_wbgt)
    if mse2>mse:
        return True
    else:
        return False


# Assume that there is a .h5 modelfile to load
def incrementalTraining(model,new_data):

    # Train the model using the new data
    X = new_data[['temperature','humidity']].values
    y = new_data['WBGT'].values
    new_model = copy.deepcopy(model)
    if compareMSE(model, new_model, X, y):
        retrained_model = retrain(model)
    else:
        print("Saving new model...")
        new_model.save('model_S50.h5')
        return

    if compareMSE(model, retrained_model, X, y):
        print("Saving old model...")
        model.save('model_S50.h5')
    else:
        print("Saving retrained model...")
        retrained_model.save('model_S50.h5')
        

if __name__ == '__main__':
    #Testing script use accordingly for the deployment
    new_data = getNewData()
    model = load_model('model_S50.h5')
    incrementalTraining(model,new_data)

