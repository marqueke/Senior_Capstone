import serial
import ztmSerialCommLibrary

ztmComms = serial.Serial(port = "COM6", baudrate=9600,
                         bytesize=8, timeout=3, stopbits=serial.STOPBITS_ONE, 
                         write_timeout = 1.0, xonxoff = True, parity = serial.PARITY_NONE)


x = ztmSerialCommLibrary.usbMsgFunctions
testCurrent = 1000
x.sendAdcTestCurrent(ztmComms, testCurrent)

rx = ztmComms.read(10)

print(rx)

# Close the serial port when done
ztmComms.close()