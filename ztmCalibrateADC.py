import serial
import serial.tools.list_ports
import ztmConversionFunctions
import ztmSerialCommLibrary #import *
from ztmSerialCommLibrary import *
import ztmConsoleFunctions
import struct
import time

# bring in external functions
ztmConv = ztmConversionFunctions.ztmConvert
ztmConsole = ztmConsoleFunctions.ztmUserInput
ztmUsb = ztmSerialCommLibrary.usbMsgFunctions

# define process constants
testCurrMax_nA = round(1.26 / (0.200000000 * 0.95), 4)   # maximum test current (nA)
testCurrMin_nA = round(1.24 / (0.200000000 * 1.05), 4)   # minimum test current (nA)

###########################################
# run start up messages

ztmConsole.adcStartMsg()

# FOR NOW, PROMPT USER TO CHECK COM PORT. LATER DEVELOPMENT - COULD CHECK COM PORT FOR THE ZTM CONTROLLER

###########################################
#### USER INPUT FUNCTIONS FOR COM PORT ####
   
###########################################
stmCOM = ztmConsole.getComPort()

attempts = 0

while(attempts < 100):  
    if(ztmConsole.checkComEntry(stmCOM)):      # check if numeric
        if(ztmConsole.confirmEntry(stmCOM)):   # confirm entry
            break                   # exit loop    
        else:
            stmCOM = ztmConsole.getNewEntry()       
    else:
        stmCOM = ztmConsole.getNewEntry()   
    attempts +=1                

stmPort = "COM" + stmCOM

print("SELECTED PORT = " + stmPort + "\n")

# CHECK IF PORT IS VALID

for port in serial.tools.list_ports.comports():
    if (port.device == stmPort):
        validPort = 1
        break      
    else:
        validPort = 0

# NOTIFY USER 

if(validPort):  # PORT IS VALID
    print(port.device + " is valid." +
          "\nConnecting...\n\n")
else:           # PORT INVALID
    print(port.device + " is not a valid COM Port.\n"+
          "Please restart the program and try again.\n"+
          "Exiting...\n")  
    
    exit()   
###########################################
####       CONNECT TO THE COM PORT     ####

ztmComms = serial.Serial(port = stmPort, baudrate=9600,
                         bytesize=8, timeout=3, stopbits=serial.STOPBITS_ONE, 
                         write_timeout = 1.0, xonxoff = True, parity = serial.PARITY_NONE)
if ztmComms.isOpen():
    ztmComms.close()
ztmComms.open()
ztmComms.isOpen()

time.sleep(1)
ztmComms.reset_output_buffer()    

###########################################
# SEND MESSAGE TO THE ZTM CONTROLLER
# TO INITIALIZE CALIBRATION PROCEDURE

attempts = 0
    # ATTEMPT TO ESTABLISH COMMUNICATION
while(attempts < 100):

    # XMIT ADC CAL MODE CMD
    ztmUsb.startAdcCalMode(ztmComms)

    # WAIT FOR MSG
    ztmUsbRx = ztmComms.read(msgBytes)

    print(ztmUsbRx)

    # CHECK FOR ACK
    if ((int(ztmUsbRx[idByte]) == MSG_E) and
        (int(ztmUsbRx[statByte]) == ztmSTATUS.STATUS_ACK.value)):
        print("Communication with ZTM Controller established.\n")
        print("---------------------------------------------\n")  

        break
    else:
        attempts +=1

if(attempts == 100):
    print("An error occurred when attempting to establish communication. Please check your connection.\n"+
          "Exiting...\n")
    ztmComms.close()
    exit()


###########################################
# GET TEST CURRENT INFORMATION

ztmConsole.adcCal0Vmsg()

attempts = 0
while(attempts < 10):
    try:
        testCurr = float(input("Please enter the Test Current as <x.xxx> and press enter: "))
        print("\n")
        testCurrStr = str(testCurr)
        if((testCurr > testCurrMin_nA) and (testCurr < testCurrMax_nA)):
            if(ztmConsole.confirmEntry(testCurrStr)):
                break
        else:
            print("Your entry was outside the acceptable range... Please try again\n")    
    except ValueError: 
        print("There was an error with your entry... Please try again\n")
    attempts += 1

if(attempts == 10):
    print("There seems to be an issue with the value of the Test Current you are attempting to enter.\n"+
          "There may be a typo on the label or you may need to remeasure the calibration current.\n"+
          "Please consult the documention for instructions on measuring the calibration current.\n\n"
          "Exiting...\n")
    ztmComms.close()
    exit()

# convert float to hex value
testCurrx = ztmConv.get_curr_int18(testCurr)

# send current to ZTM Controller
ztmUsb.sendAdcTestCurrent(ztmComms, testCurrx)

# check if STM received correct data
ztmUsbRx = ztmComms.read(msgBytes)

for byte in ztmUsbRx:
    print(hex(byte))

currTemp = ((ztmUsbRx[5] << 16) | (ztmUsbRx[4] << 8) | (ztmUsbRx[3]))
fCurr = ztmConv.get_curr_float_nA(currTemp)
print(fCurr)
if((testCurr - 0.01) <= fCurr <= (testCurr + 0.01)):
    print("ok\n")
###########################################
# CALIBRATE THE 0V OFFSET
    # ERROR CHECK THE MEASUREMENT, IT SHOULD BE WITHIN RANGE
ztmConsole.adcCal0Vmsg()

attempts = 0
entryTarget = "ready"
while(attempts < 10):
    try:
        userCmd = (input("Please confirm when the microscope is set up to take the 0V\n"+
                         "calibration measurements by typing 'ready' and pressing <enter>: "))
        print("\n")
        
        if(userCmd.lower() == entryTarget.lower()):
            break
        else:
            print("There was an error with your entry... Please try again\n")    
    except ValueError: 
        print("There was an error with your entry... Please try again\n")
    attempts += 1

if(attempts == 10):
    print("Please attempt the calibration procedure again when you are ready.\n"
          "Exiting...\n")
    ztmComms.close()
    exit()

ztmUsb.adcCalCmd_0V(ztmComms)

###########################################
# CALIBRATE THE LINEAR GAIN ERROR
#     # ERROR CHECK THE MEASUREMENT, IT SHOULD BE WITHIN RANGE 
ztmComms.close()