import serial
import struct
import threading
from enum import Enum
from ztmSerialCommLibrary import *
from value_conversion import Convert
import time
import datetime
#ztmUsb = ztmSerialCommLibrary.usbMsgFunctions

#define conversion functions
#ztmConvert = ztmConversionFunctions.ztmConvert

###########################################################################
# set this to True to enable serial port
testFunc = False
###########################################################################
#define global constants
usbDelay = 0.05

nmPerVolt       = 20    # vpiezo distance / volt conversion
nmPerEighthStep = 53    # approx. average distance / eighth step


FULL_STEP       = 0x00
HALF_STEP       = 0X01
QUARTER_STEP    = 0X02
EIGHTH_STEP     = 0X03

DIR_UP          = 0X00
DIR_DOWN        = 0X01

###########################################################################
# EXAMPLE MESSAGE - USES usbMsgFunctions.unpackRxMsg() TO DECODE
###########################################################################
# IN ACTUAL PROGRAM, ADD MORE LOGIC TO LOAD RESULTS OF MSG READ INTO PROPER VARIABLES 
###########################################################################
#testMsg = [MSG_A, ztmCMD.CMD_CLR.value, ztmSTATUS.STATUS_MEASUREMENTS.value, 0X00, 0X00, 0X00, 0X00, 0x00, 0x00, 0x00, 0x00] 
#    # values of interest
#testCurrent = 2.547895322   # Example float value to pack into bytes
#vB = 4.5                    # example vbias V from gui
#vP = 6.7                    # example vpiezo V from gui
#
## Pack the floats into bytes objects
#testCurrBytes = struct.pack('f', testCurrent)
#vbiasBytes = struct.pack('H', ztmConvert.get_Vbias_int(vB))
#vpzoBytes = struct.pack('H', ztmConvert.get_Vpiezo_int16(vP))
#
## load them into the dummy message
#testMsg[3:7]  = list(testCurrBytes)
#testMsg[7:9]  = list(vbiasBytes)
#testMsg[9:11] = list(vpzoBytes)
#
#results = usbMsgFunctions.unpackRxMsg(testMsg)
#
#print(results)

###########################################################################
# OPEN THE COM PORT TO BEGIN TESTING
if testFunc:
    # get the com port
    ztmPort = usbMsgFunctions.getComPort()
    print(ztmPort)
    # connect to the com port
    ztmComms = usbMsgFunctions.connectComPort(ztmPort)
    if(ztmComms == False):
        exit()
    # ensure that MCU is in its regular operational state

##########################################################################          
# CONSOLE & FILE FUNCTIONS FOR RUNNING TEST CASES
def testStart():
    attempts = 0
    entryTarget = "start"
    while(attempts < 10):
        try:
            userCmd = (input("Enter <start> to being running the test case: "))
            print("\n")

            if(userCmd.lower() == entryTarget.lower()):
                return True
            else:
                print("There was an error with your entry... Please try again\n")    
        except ValueError: 
            print("There was an error with your entry... Please try again\n")
        attempts += 1
    if attempts == 10:
        return False    
    
def getResults():
    result = input("Enter the desired test data into the console: ")
    print("\n")
    return result    
    
def waitForNext():
    attempts = 0
    entryTarget = "start"
    while(attempts < 10):
        try:
            userCmd = (input("Enter <start> to continue the test: "))
            print("\n")
            if(userCmd.lower() == entryTarget.lower()):
                return True
            else:
                print("There was an error with your entry... Please try again\n")    
        except ValueError: 
            print("There was an error with your entry... Please try again\n")
        attempts += 1
    if attempts == 10:
        return False 

def printTestCase(testCase):
    print(f"Running Test Case {testCase}\n")

def printCondition(testCondition):    
    print(f"Conditions: {testCondition}\n")

class testLogFiles():
    def __init__(self):
        self.testLogPath = None


    def openTestLog(self, testCase, ztmComms):
        print("############################\n")
        printTestCase(testCase)
        self.testLogPath = f"Test Results - {testCase}.txt"
        with open(self.testLogPath, 'w') as file:
            file.write(f"TEST CASE: {testCase}\n")
            timeStamp = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            file.write(f"Starting at : {timeStamp}\n")
            file.write(f"Baudrate: {ztmComms.baudrate}\n")
            file.write("##########################################################################\n")
            file.close()

    def logTestItem(self, note):
        with open(self.testLogPath, 'a') as file:
            file.write(f"{note}\n")
            file.close()

    def logTestResponse(self, response):
        printCondition(f"Response : {response}\n")
        timeStamp = f"{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}\n"
        with open(self.testLogPath, 'a') as file:
            file.write("\n")
            file.write(f"MCU Response: {response} -- {timeStamp}\n")
            file.close()

    def logTestResults(self, result, testCondition):
        printCondition(f"{testCondition} : {result}\n")
        with open(self.testLogPath, 'a') as file:
            file.write("\n")
            file.write(f"Condition: {testCondition}\n")
            timeStamp = f"{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]},\n"
            file.write(f"Result: {result} -- {timeStamp}\n")
            file.close()

    def logTestExpected(self, expected):
        printCondition(f"Expected : {expected}\n")
        with open(self.testLogPath, 'a') as file:
            file.write("\n")
            file.write(f"Expected: {expected}\n")
            file.write("----------\n")
            file.close() 


    def testDone(self):
        print("Test done...\n-------------\n")
        with open(self.testLogPath, 'a') as file:
            file.write("\n")
            file.write(f"Test Complete\n")
            file.write(f"##########################################################################\n")
            file.close() 

    def fileClose(self, file):
        file.close()

def initMCU(ztmComms):
    print("Initializing communication with microcontroller.")
    noDone = True
    try:
        usbMsgFunctions.sendMsgC(ztmComms, ztmCMD.CMD_CLR.value, ztmSTATUS.STATUS_RDY.value)
        #if(usbMsgFunctions.unpackRxMsg(usbMsgFunctions.ztmGetMsg(ztmComms)) == ztmSTATUS.STATUS_ACK.value):
         #   noDone = False    
    except serial.SerialException as e:
        print(f"Initialization operation failed: {e}")    
        return False
    return True 

def checkDONE(ztmComms): 
    attempts = 0
    while attempts < 10:    
        try:
            response = usbMsgFunctions.unpackRxMsg(usbMsgFunctions.ztmGetMsg(ztmComms))
            if(response == ztmSTATUS.STATUS_DONE.value): 
                break           

            elif(response == ztmSTATUS.STATUS_NACK.value):
                attempts += 1

            else:
                attempts += 1
        except serial.SerialException as e:
            attempts += 1
            print(f"Failure: {e}")    
            return False
    if attempts == 10:
        return False
    else:    
        return ztmSTATUS(response).name


#################################################################################################################################
# CALIBRATE THE LINEAR GAIN ERROR



#    response = ztmComms.read(msgBytes)
#    if(response[2] ==  ztmSTATUS.STATUS_DONE.value):
#        noDone = False
#        print("ACK Rcvd\n")
# STEPPER MOTOR TEST
#usbMsgFunctions.sendMsgC(ztmComms,ztmCMD.CMD_CLR.value, ztmSTATUS.STATUS_RDY.value)
#time.sleep(2)
#usbMsgFunctions.sendMsgD(ztmComms, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, FULL_STEP, DIR_UP, 425)
#time.sleep(4)
#usbMsgFunctions.sendMsgD(ztmComms, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, FULL_STEP, DIR_DOWN, 425)
#time.sleep(4)
#usbMsgFunctions. sendMsgC(ztmComms, ztmCMD.CMD_STEPPER_RESET_HOME_POSITION.value, ztmSTATUS.STATUS_CLR.value)
#usbMsgFunctions.sendMsgC(ztmComms,ztmCMD.CMD_RETURN_TIP_HOME.value, ztmSTATUS.STATUS_ACK.value)
#noDone = True
#while(noDone):
#    response = ztmComms.read(msgBytes)
#    if(response[2] ==  ztmSTATUS.STATUS_DONE.value):
#        noDone = False
#        print("ACK Rcvd\n")

#usbMsgFunctions.sendMsgA(ztmComms, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_CLR.value, 0, 0, 2.5)

########################################################################## 
## measurements test
#usbMsgFunctions.sendMsgC(ztmComms,ztmCMD.CMD_CLR.value, ztmSTATUS.STATUS_RDY.value)
#noDone = True
#while(noDone):
#    if(usbMsgFunctions.unpackRxMsg(usbMsgFunctions.ztmGetMsg(ztmComms)) == ztmSTATUS.STATUS_ACK.value):
#        noDone = False
#        print("ACK Rcvd\n")
#time.sleep(1)
#usbMsgFunctions.sendMsgX(ztmComms, ztmCMD.CMD_DAC_CAL_CLEAR_VBIAS.value, 0.0, 0, 0)
#usbMsgFunctions.sendMsgA(ztmComms, ztmCMD.CMD_SET_VBIAS.value, ztmSTATUS.STATUS_CLR.value, 0, 0, 0)
#usbMsgFunctions.sendMsgA(ztmComms, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_CLR.value, 0, 0, 2.5)

#time.sleep(2)

#usbMsgFunctions.sendMsgA(ztmComms, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_CLR.value, 0, 0, 0)



#
#time.sleep(1)
#count = 0
###
##print("sending msmt cmd\n")
#usbMsgFunctions.sendMsgC(ztmComms,ztmCMD.CMD_REQ_FFT_DATA.value, ztmSTATUS.STATUS_CLR.value)
#
#### GET 10 MEASUREMENTS
#while(count < 10):
#    usbMsgFunctions.sendMsgC(ztmComms,ztmCMD.CMD_REQ_DATA.value, ztmSTATUS.STATUS_CLR.value)
#    results = usbMsgFunctions.unpackRxMsg(ztmComms.read(msgBytes))
#    print(count)
#    print(results)
#    count = count + 1
##

#noDone = True
#while(noDone):
#    if(usbMsgFunctions.unpackRxMsg(usbMsgFunctions.ztmGetMsg(ztmComms)) == ztmSTATUS.STATUS_ACK.value):
#        noDone = False
#        print("ACK Rcvd\n")

########################################################################## 
### START/STOP SINUSOID TEST
#usbMsgFunctions.sendMsgC(ztmComms,ztmCMD.CMD_CLR.value, ztmSTATUS.STATUS_RDY.value)
###
#if(usbMsgFunctions.unpackRxMsg(usbMsgFunctions.ztmGetMsg(ztmComms)) == ztmSTATUS.STATUS_ACK.value):
#    print("ACK RCVD")
#else:
#    print("oops\n")    
#
#time.sleep(2)
#noDone = True
#usbMsgFunctions.sendMsgE(ztmComms, 3.2, 2001)

#while(noDone):
#    if(usbMsgFunctions.unpackRxMsg(usbMsgFunctions.ztmGetMsg(ztmComms)) == ztmSTATUS.STATUS_ACK.value):
#        noDone = False
#        print("ACK Rcvd\n")
#        
#print("set output\n")  

#noDone = True
#usbMsgFunctions.sendMsgC(ztmComms,ztmCMD.CMD_VBIAS_STOP_SINE.value, ztmSTATUS.STATUS_CLR.value)
#while(noDone):
#    if(usbMsgFunctions.unpackRxMsg(usbMsgFunctions.ztmGetMsg(ztmComms)) == ztmSTATUS.STATUS_ACK.value):
#        noDone = False
#        print("ACK Rcvd\n")


#x = struct.pack('H', ztmConvert.get_Vbias_int(10.0))
#usbMsgFunctions.sendMsgD(ztmComms, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, FULL_STEP, DIR_UP, 1000)
#time.sleep(10)
#usbMsgFunctions.sendMsgD(ztmComms, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, FULL_STEP, DIR_DOWN, 1000)
#usbMsgFunctions.sendMsgA(ztmComms,ztmCMD.CMD_SET_VBIAS.value, ztmSTATUS.STATUS_CLR.value, 0, 2.2, 0)

#msgCmd = 0x3
#uint16_rateHz = 1000
#payload = bytes(payloadBytes - 2) 
#payload = bytes(2)
#msgStatus = 0x1
#current_nA = 1.2
#vbias = 1.5
#vpzo = 2.5
#size = 0x1
#dir = 0x0
#count = 100000
#sineVbiasAmp = 1.2
#
#sineVbiasBytes = struct.pack('H', ztmConvert.get_Vbias_int(sineVbiasAmp))
#rateHzBytes = struct.pack('H', uint16_rateHz)
#payloadByteLen = payloadBytes - 4
#payload = bytes(4)
#messageE = struct.pack('<BBBHHBBBB', MSG_E, ztmCMD.CMD_VBIAS_SET_SINE.value, ztmSTATUS.STATUS_CLR.value, 
#                               ztmConvert.get_Vbias_int(sineVbiasAmp)
#                               , uint16_rateHz, *payload)
#
input4Bytes = 0.9960627641711539
msgCmd = ztmCMD.CMD_SET_VBIAS.value
vbiasTx_V = 5
vpiezoTx_V = 5.7

headerX = [MSG_X, msgCmd, ztmSTATUS.STATUS_CLR.value]
if(msgCmd == ztmCMD.CMD_PIEZO_ADJ.value):
    # offset is an integer
    Tx4Bytes = struct.pack('i', input4Bytes)
else:
    Tx4Bytes = struct.pack('f', input4Bytes)
if(msgCmd == ztmCMD.CMD_SET_VBIAS.value):
    # pack the value directly without conversion
    vbiasBytes = struct.pack('h', vbiasTx_V)
else:
    # convert the float voltage to code
    vbiasBytes = struct.pack('H', Convert.get_Vbias_int(vbiasTx_V))

vpzoBytes = struct.pack('H', Convert.get_Vpiezo_int(vpiezoTx_V))

messageX = struct.pack('<BBB4s2s2s', MSG_X, msgCmd, ztmSTATUS.STATUS_CLR.value, Tx4Bytes, vbiasBytes, vpzoBytes)

#
#
##messageB = struct.pack('<BBBHBBBBBB', MSG_B, msgCmd, msgStatus, uint16_rateHz, *payload)
##messageD = struct.pack('<BBBBBiBB', MSG_D, msgCmd, msgStatus, size, dir, count, *payload)
for byte in messageX:
    print(hex(byte))

print("length = "+ f"{len(messageX)}")

vb = Convert.get_Vbias_int(.001467) - 0x8000
print(vb)
vbiasBytes = struct.pack('h', vb)
print(vbiasBytes)
if(testFunc):
    ztmComms.close()