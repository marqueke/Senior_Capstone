ser = serial.Serial(port='COM7', baudrate=9600)

while True:
    value = ser.readline()
    valueInString=str(value, 'UTF-8')
    print(valueInString)