from enum import Enum
#from dataclasses import dataclass, field
#import numpy as np
import serial
import time

MSG_A = 0x0A
MSG_B = 0x0B
MSG_C = 0x0C
MSG_D = 0x0D
MSG_E = 0x0E
MSG_F = 0x0F

msgBytes = 11

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
    CMD_SET_VBIAS, \
    CMD_SET_ADC_SAMPLE_RATE, \
    CMD_PERIODIC_DATA_ENABLE, \
    CMD_PERIODIC_DATA_DISABLE, \
    CMD_REQ_DATA, \
    CMD_REQ_STEP_COUNT, \
    CMD_STEPPER_ADJ, \
    CMD_PIEZO_ADJ, \
    CMD_VBIAS_SET_SINE, \
    CMD_VBIAS_STOP_SINE, \
    CMD_REQ_FFT_DATA, \
    CMD_RETURN_TIP_HOME, \
    CMD_STEPPER_RESET_HOME_POSITION, \
    CMD_ABORT = range(0 , 15)

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
    STATUS_ERROR, \
    STATUS_STEP_COUNT, \
    STATUS_MEASUREMENTS, \
    STATUS_FFT_DATA, \
    STATUS_TIP_CRASHED = range(0 , 14)


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
