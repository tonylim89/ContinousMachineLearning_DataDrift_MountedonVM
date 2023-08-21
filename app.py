
from flask import Flask,request,jsonify
from keras.models import load_model
from model import predictModel,min_max_day,xDayForecast
from script import getDataFrame, actual_data, all_actual_data
from mseScript import getMSE

app = Flask(__name__)

# Get X hour predicted WBGT (15min instance of each hour)
@app.route('/predict',methods=['GET'])
def predict():
    # Can do it using /predict/{hour} perhaps
    input = request.args.get('hour',type=int)
    # Assume station_id is S43 temporary
    station_id = request.args.get('station_id',type=str)
    # Get correct saved model file
    modelName = 'model_' + station_id + '.h5'

    # Load the model
    modelA = load_model(modelName)

    df = getDataFrame(station_id)
    
    # Check if the input time is valid (non-negative integer)
    if not isinstance(input, int) or input < 0:
        return jsonify({'error': 'Invalid input. Please provide a non-negative integer value for time.'})

    return jsonify(predictModel(modelA,input,df))


# Get the current WBGT for the specific station_id
@app.route('/current',methods=['GET'])
def actual():
    station_id = request.args.get('station_id',type=str)
    json_data = actual_data(station_id).to_json(orient='records',date_format='iso')

    return jsonify(json_data)

# Get the current WBGT for all stations
@app.route('/all_current',methods=['GET'])
def all_actual():
    json_data = all_actual_data().to_json(orient='records',date_format='iso')
    return jsonify(json_data)

# Get the MSE via backtracking using 24hr prediction window
@app.route('/mse',methods=['GET'])
def mse():
    station_id = request.args.get('station_id',type=str)

    modelName = 'model_' + station_id + '.h5'

    modelA = load_model(modelName)

    return jsonify(getMSE(modelA,station_id))

# Get the X day prediction using historical data, return only Min and Max
@app.route('/day_forecast',methods=['GET'])
def day_forecast():
    station_id = request.args.get('station_id',type=str)
    day = request.args.get('day',type=int)

    modelName = 'model_' + station_id + '.h5'

    modelA = load_model(modelName)

    json_data = min_max_day(xDayForecast(modelA,day,station_id)).to_json(orient='records',date_format='iso')
    return jsonify(json_data)
    

if __name__ == '__main__':
    app.run(host = "0.0.0.0", port = "5000")
