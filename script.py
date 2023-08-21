import mysql.connector as mysql
import configparser
import pandas as pd
from datetime import datetime, timedelta


# Get the filtered DF of a specific station - reduce time complexity
def getDataFrame(station_id):
    
    connection = sql_connection()
    cursor = connection.cursor()

    query = f"SELECT * FROM temperature_data WHERE station_id = '{station_id}'"

    cursor.execute(query)

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    columns = [i[0] for i in cursor.description]
    df = pd.DataFrame(result,columns=columns)

    # Preprocessing
    df.drop_duplicates(subset=['timestamp'], keep='first', inplace=True)
    df.drop(columns=['id'],inplace=True)
    
    # Convert Timeframe from String to Date object
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Apply the custom function to create the 'WBGT' column
    df['WBGT'] = df.apply(lambda row: calculate_wbgt(row['temperature'], row['humidity']), axis=1)

    return df

# Define a custom function for WBGT calculation
def calculate_wbgt(temperature, humidity):
    
    # Obtained from Linear Regression model
    WBGT = 1.29 * temperature + 0.18 * humidity + -18.53

    return WBGT

def sql_connection():
    # Managing config

    config = configparser.ConfigParser()
    config.read('configuration.ini')

    db_host = config['mysql']['host']
    db_user = config['mysql']['user']
    db_password = config['mysql']['password']
    db_port = config['mysql']['port']
    db_name = config['mysql']['database']

    # Database connection details

    connection = mysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
        
    )
    return connection

# Get our sql data generated by our cron job script which has a more consistent 1 minute interval timeframe
def actual_data(station_id):
    connection = sql_connection()
    cursor = connection.cursor()

    query = "SELECT station_id,temperature,humidity,timestamp FROM temperature_data WHERE (station_id, timestamp) IN (SELECT station_id, MAX(timestamp) FROM temperature_data GROUP BY station_id);"

    df = sqlCursorDFCode(cursor,query,connection)

    # Create WBGT Category column
    df['Category'] = df.apply(lambda row: getWBGTCategory(row['WBGT']),axis=1)

    # Filter by given station_id
    
    filter = df['station_id'] == station_id
    
    filtered_df = df[filter]

    return filtered_df

# Get the DF of all stations
def all_actual_data():
    connection = sql_connection()
    cursor = connection.cursor()

    query = "SELECT station_id,temperature,humidity,timestamp FROM temperature_data WHERE (station_id, timestamp) IN (SELECT station_id, MAX(timestamp) FROM temperature_data GROUP BY station_id);"

    df = sqlCursorDFCode(cursor,query,connection)

    # Create WBGT Category column
    df['Category'] = df.apply(lambda row: getWBGTCategory(row['WBGT']),axis=1)

    return df

# Logic to deal with generating backtracked data and obtaining it from our actual values in our DF
def getDataForSpecificTime(station_id, timestamp):
    connection = sql_connection()
    cursor = connection.cursor()

    # To obtain only the date to reduce the time complexity to search the sql data
    day = timestamp.date()

    # To cater for exceeding the current day
    new_date = day - timedelta(days=1)

    # Calculate the end point of the 24-hour interval from the given time
    end_time = timestamp - timedelta(hours=24)

    query = f"SELECT * FROM temperature_data WHERE station_id = '{station_id}' AND timestamp BETWEEN '{end_time}' AND '{timestamp}'"

    return sqlCursorDFCode(cursor,query,connection)

# Deal with the backtracking calcuation of time for MSE
def getTimestamp():
    current_time = datetime.now()

    # In this case it is wise to set specific intervals within a day to reduce programming resources
    backtracked_time = current_time - timedelta(hours=24)

    # Round off to nearest second
    rounded_backtracked_time = backtracked_time.replace(second=0, microsecond=0)

    return rounded_backtracked_time

# Deal with category sorting of WBGT values
def getWBGTCategory(WBGT):
    if WBGT <30:
        return "White"
    elif WBGT <31:
        return "Green"
    elif WBGT <32:
        return "Yellow"
    elif WBGT <33:
        return "Red"
    else:
        return "Black"
    

def getXDayStartTimestamp(day):

    current_time = datetime.now()
    backtracked_time = current_time - timedelta(days=day)

    # Trying to get the entire day
    backtracked_time = backtracked_time.replace(hour=0, minute=0, second=0, microsecond=0)

    return backtracked_time

def getXDayEndTimestamp(day):

    current_time = datetime.now()
    end_time = current_time - timedelta(days=1)

    # Trying to get the entire day
    end_time = end_time.replace(hour=23, minute=59, second=59, microsecond=0)

    return end_time



def getXDaySpecificDF(station_id, startTimestamp,endTimestamp):

    connection = sql_connection()
    cursor = connection.cursor()

    query = f"SELECT * FROM temperature_data WHERE station_id = '{station_id}' AND timestamp >= '{startTimestamp}' AND timestamp <= '{endTimestamp}'"

    df = sqlCursorDFCode(cursor,query,connection)

    return df


# Reduce repeated codes
def sqlCursorDFCode(cursor,query,connection):
    cursor.execute(query)

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    columns = [i[0] for i in cursor.description]
    df = pd.DataFrame(result, columns=columns)

    # Apply the custom function to create the 'WBGT' column
    df['WBGT'] = df.apply(lambda row: calculate_wbgt(row['temperature'], row['humidity']), axis=1)

    return df
