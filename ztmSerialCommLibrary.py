from enum import Enum
#from dataclasses import dataclass, field
#import numpy as np
import serial
import time
<<<<<<< HEAD
MSG_A = 0X0A
MSG_E = 0X0E
MSG_F = 0X0F
=======

MSG_A = 0x0A
MSG_B = 0x0B
MSG_C = 0x0C
MSG_D = 0x0D
MSG_E = 0x0E
>>>>>>> kelseys_GUI

msgBytes = 10

usbDelay  = 0.05

### USB MESSAGE FORMAT
# -header-
idByte      = 0    # MSG ID -> 1 byte
cmdByte     = 1    # CMD    -> 1 byte
statByte    = 2    # STATUS -> 1 byte
    # -payload-
    # adc curr[0] 
    # adc curr[1]
    # adc curr[2]
    # vbias[0]
    # vbias[1]
    # vpzo[0]
    # vpzo[1]

class ztmCMD(Enum): 
    CMD_CLR, \
    CMD_VBIAS_SET, \
    CMD_CURR_SETPT, \
    CMD_SCOPE_START, \
    CMD_SCOPE_HALT, \
    CMD_TIP_RETRACT, \
    CMD_TIP_UP, \
    CMD_TIP_DWN, \
    CMD_SET_SAMPLE_RATE, \
    CMD_IZ_MODE, \
    CMD_IV_MODE , \
    CMD_IZ_PARAM_STORE, \
    CMD_IZ_SWP_START, \
    CMD_IZ_SWP_STOP , \
    CMD_IV_PARAM_STORE, \
    CMD_IV_SWP_START, \
    CMD_IV_SWP_STOP, \
    CMD_ABORT , \
    CMD_ADC_CAL_MODE , \
    CMD_ADC_CAL_LOAD_CURR , \
<<<<<<< HEAD
    CMD_ADC_CAL_MEAS_0V , \
    CMD_ADC_CAL_MEAS_TEST_CURR = range(0 , 22)
=======
    CMD_ADC_CAL_MEAS_GND , \
    CMD_ADC_CAL_MEAS_TEST_CURR, \
    CMD_ADC_CAL_STOP, \
    CMD_DAC_CAL_MODE_VBIAS, \
    CMD_DAC_CAL_MODE_VPZO, \
    CMD_DAC_CAL_SET_0V, \
    CMD_DAC_CAL_STORE_0V, \
    CMD_DAC_CAL_SET_MID_SCALE, \
    CMD_DAC_CAL_STORE_MID_SCALE, \
    CMD_DAC_CAL_CHECK, \
    CMD_DAC_CAL_STOP = range(0 , 31)
>>>>>>> kelseys_GUI

class ztmSTATUS(Enum):
    STATUS_ACK, \
    STATUS_NACK, \
    STATUS_DONE, \
    STATUS_FAIL, \
    STATUS_RESEND, \
    STATUS_OVERCURRENT, \
    STATUS_CLR, \
    STATUS_RDY, \
    STATUS_BUSY, \
    STATUS_ERROR = range(0 , 10)

<<<<<<< HEAD
class usbMsgFunctions:
    def __init__(self,val):
        self.val=val

    def startAdcCalMode(ztmComms):
        ''' send data byte by byte'''

        MsgId   = [0xf]
        CmdByte = [ztmCMD.CMD_ADC_CAL_MODE.value]
        padByte = [0x0]

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)

        for i in range(0, 8):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)
        # clear buffer    
        ztmComms.flush()

    def sendAdcTestCurrent(ztmComms, testCurrent):
        ''' send data byte by byte'''

        MsgId   = [0xf]
        CmdByte = [ztmCMD.CMD_ADC_CAL_LOAD_CURR.value]
        padByte = [0x0]
      
        # extract bytes
        testCurrBytes = [0, 0, 0]
        testCurrBytes[0] =  testCurrent & 0x0000FF
        testCurrBytes[1] = (testCurrent >> 8) & 0x0000FF
        testCurrBytes[2] = (testCurrent >> 16) & 0x0000FF
        #debug
            # Print each element of testCurrBytes in hexadecimal format
        #print([hex(byte) for byte in testCurrBytes])

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)

        # send empty Status
        ztmComms.write(serial.to_bytes(padByte))
        time.sleep(usbDelay)        

        #send current
        for byte in testCurrBytes:
            ztmComms.write(serial.to_bytes([byte]))
            time.sleep(usbDelay)

        for i in range(0, 4):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)

        # clear buffer    
        ztmComms.flush()

    def adcCalCmd_0V(ztmComms):
        ''' send data byte by byte'''

        MsgId   = [0xf]
        CmdByte = [ztmCMD.CMD_ADC_CAL_MEAS_0V.value]
        padByte = [0x0]

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)

        for i in range(0, 8):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)

        # clear buffer    
        ztmComms.flush()
        
=======

# the usbMsgFunctions could probably all be replaced by a single elaborate function that 
# allows the user to select the msg/cmd/status/payload values, but for simplicity & speed of 
# development a different function was made for each message used in the cal procedure
class usbMsgFunctions:
    def send_command(ztmComms, MsgId, CmdByte, Payload=[]):
        message = [MsgId, CmdByte] + Payload + [0x00] * (msgBytes - 3 - len(Payload))
        message = serial.to_bytes(message)
        ztmComms.write(message)
        time.sleep(usbDelay)
        ztmComms.flush()
>>>>>>> kelseys_GUI
