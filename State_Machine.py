from enum import Enum, auto
import struct
from value_conversion import Convert 
from ztmSerialCommLibrary import ztmCMD, ztmSTATUS, usbMsgFunctions, MSG_A, MSG_B, MSG_C, MSG_D, MSG_E, MSG_F

# need to be modified to include send/receive commands and data
class MainState(Enum):
    ZTM_ST_HOME = auto()            # go to IDLE, wait for CMDs - START, STOP, FINE ADJ, SET PARAMS, IZ MODE, IV MODE, STEPPER RESET, SET SAMPLE RESET          
    ZTM_ST_IZ_SWEEP = auto()        # go to WAIT, wait for CMDs - SET PARAMS, START SWEEPM STOP SWEEP, RETURN HOME  
    ZTM_ST_IV_SWEEP = auto()        # go to WAIT, wait for CMDs - SET PARAMS, START SWEEPM STOP SWEEP, RETURN HOME   
    ZTM_ST_ERROR = auto()           # something is wrong with the system
    ZTM_ST_TIP_CRASHED = auto()     # shut down peripherals, return tip to home, wait for user to reset
    
    #ZTM_STATE_COUNT = auto()       # number of main states

class SubState(Enum):
    # Home substates
    HOME_ST_IDLE = auto()                       # wait for CMDs- rcv ADC measurements
    HOME_ST_CURRENT_APPROACH_ACTIVE = auto()    # controller engaged in moving tip to current setpoint, wait for CMDs - HALT, RETRACT, SET_VBIAS (return to ST_IDLE when setpoint reached)
    HOME_ST_CURRENT_APPROACH_PAUSED = auto()    # tip approach is paused, wait for CMDs - START, RETURN HOME, respond to other CMDs with STATUS_BUSY
    HOME_ST_FINE_ADJ_UP = auto()                # move tip to a defined distance UP; return to ST_IDLE
    HOME_ST_FINE_ADJ_DOWN = auto()              # move tip to a defined distance DOWN; return to ST_IDLE
    HOME_ST_RESET_HOME_POSITION = auto()        # set tip to a new home position 
    HOME_ST_TIP_RETURN = auto()                 # move tip to home position; if HALT received, halt tip, await next CMD
    # IZ sweep substates
    IZ_ST_SWEEP_WAITING = auto()                # wait for CMDs- SET PARAMS, START SWEEP, STOP SWEEP, RETURN HOME
    IZ_ST_SWEEP_SETUP = auto()                  # SET PARAMS, return to WAIT
    IZ_ST_SWEEP_ACTIVE = auto()                 # perform sweep, transmit measurements; if STOP rcvd, pause process, go to SWEEP_DONE when sweep complete
    IZ_ST_SWEEP_PAUSED = auto()                 # wait for CMDs - START SWEEP, RETURN HOME; return to SWEEP_ACTIVE if START_SWEEP rcvd
    IZ_ST_SWEEP_RESET = auto()                  # clear the process
    IZ_ST_SWEEP_DONE = auto()                   # return to SWEEP_WAITING
    # IV sweep substates
    IV_ST_SWEEP_WAITING = auto()                # wait for CMDs - SET PARAMS, START SWEEP, STOP SWEEP, RETURN HOME
    IV_ST_SWEEP_SETUP = auto()                  # SET PARAMS, return to SWEEP_WAITING
    IV_ST_SWEEP_ACTIVE = auto()                 # perform sweep, transmit measurements; if STOP rcvd, pause process, go to SWEEP_DONE when sweep complete
    IV_ST_SWEEP_PAUSED = auto()                 # wait for CMDs - START SWEEP, RETURN HOME; return to SWEEP_ACTIVE if START_SWEEP rcvd
    IV_ST_SWEEP_RESET = auto()                  # clear the process
    IV_ST_SWEEP_DONE = auto()                   # return to SWEEP_WAITING
    
    #SUBSTATE_COUNT = auto()        # number of subtates

class DataCtrl:
    def __init__(self, callback):
        self.callback = callback
        self.state = MainState.ZTM_ST_HOME
        self.substate = SubState.HOME_ST_IDLE

    def decode_data(self, raw_data):
        '''
        Reads and decodes the data sent by the MCU
        '''
        if len(raw_data) < 11:
            print("Incomplete data frame received.")
            return None

        header = struct.unpack('BBB', raw_data[:3])
        payload = raw_data[3:]

        msg = header[0]
        cmd = header[1]
        status = header[2]

        print(f"Decoded Header: MSG={msg}, CMD={cmd}, STATUS={status}, PAYLOAD={payload}")
    
    def send_command(self, msg, cmd, status, payload):
        '''
        Writes data to send to the MCU
        '''
        data = struct.pack('BBB', msg, cmd, status) + payload
        print(f"Sending command: {data.hex()}")
        self.serial_ctrl.write_bytes(data) 
    
    def DataMachine(self, raw_data):
        '''
        ADC current (float) = 0 nA
        Vbias (int) = 0 V
        Vpzo (int) = 0 V
        Baud rate (int) = 0 Hz
        Step size (int) = 0
        Direction (int) = 0
        Number of steps (int) = 0
        Vbias sine (int) = 0
        Frequency (int) = 0 Hz
        FFT Current Amplitude (float) = 0 nA
        FFT Frequency (float) = 0 Hz
        '''
        header = struct.unpack('BBB', raw_data[:3])
        payload = raw_data[3:]

        msg = header[0]
        cmd = header[1]
        status = header[2]
        
        decoded_data = self.decode_data(raw_data)
        if not decoded_data:
            return
        
        # HOME main state
        if self.state == MainState.ZTM_ST_HOME and self.substate == SubState.HOME_ST_IDLE:
            if msg == MSG_A:
                # go to handle msg A
                pass
            if msg == MSG_B:
                # go to handle msg B
                pass
        # IZ main state
        if self.state == MainState.ZTM_ST_IZ_SWEEP:
            self.substate == SubState.IZ_ST_SWEEP_WAITING
        # IV main state
        if self.state == MainState.ZTM_ST_IV_SWEEP:
            self.substate == SubState.IV_ST_SWEEP_WAITING
        # Error in system main state
        if self.state == MainState.ZTM_ST_ERROR:
            '''
            Error msg, abort system
            '''
            pass
        # Tip crashed main state
        if self.state == MainState.ZTM_ST_TIP_CRASHED:
            '''
            Error msg, shut down peripherals and reset
            '''
            pass
    
        