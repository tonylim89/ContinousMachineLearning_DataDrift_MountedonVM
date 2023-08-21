from model import trainModel
'''
stations = ['S106','S116','S44','S24','S109','S121','S43','S50','S60','S104','S107','S111','S115','S117']

for station in stations:
    print(f'Now training for {station}')
    trainModel(station)
    if(station == 'S117'):
        print("Training completed")

'''
trainModel('S50')