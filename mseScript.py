from script import getTimestamp, getDataForSpecificTime
from model import predictGivenTimestamp, cleanActualData, MSE

def getMSE(model, station_id):

    # Get the X hour ahead time from current time that requested the MSE
    givenTime = getTimestamp()

    # Obtain the DF for actual values from X ahead time to current time (Backtrack method)
    actualdf = getDataForSpecificTime(station_id,givenTime)

    # Obtain predicted value for the DF from X ahead time to current time
    predicted_data_df = predictGivenTimestamp(model,givenTime,actualdf)

    # Obtain only the needed wbgt values for comparision, and check the size is the same
    cleanActualData_df = cleanActualData(givenTime,actualdf)

    # Return the MSE calculated using this two values
    return MSE(predicted_data_df,cleanActualData_df)



    

