from enum import Enum
#from dataclasses import dataclass, field
#import numpy as np
import serial
import time

MSG_A = 0X0A
MSG_E = 0X0E
MSG_F = 0X0F

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
