from enum import Enum
import struct
from value_conversion import Convert
#from dataclasses import dataclass, field
#import numpy as np
import serial
import time

import GLOBALS
###########################################
adcByteLen = 4
dacByteLen = 2
vByteLen = GLOBALS.PAYLOAD_BYTES - adcByteLen

padByte = [0x00]

usbDelay  = 0.05
###########################################
### USB MESSAGE FORMAT
# -header-
idByte      = 0    # MSG ID -> 1 byte
cmdByte     = 1    # CMD    -> 1 byte
statByte    = 2    # STATUS -> 1 byte

# Note: Add CMD_SET_SAMPLE_SIZE
class ztmCMD(Enum): 
    CMD_CLR	, \
    CMD_SET_VBIAS,   \
    CMD_SET_ADC_SAMPLE_RATE	,   \
    CMD_SET_ADC_SAMPLE_SIZE,    \
    CMD_PERIODIC_DATA_ENABLE	,   \
    CMD_PERIODIC_DATA_DISABLE	,   \
    CMD_REQ_DATA	,   \
    CMD_REQ_STEP_COUNT	,   \
    CMD_STEPPER_ADJ	,   \
    CMD_PIEZO_ADJ	,   \
    CMD_VBIAS_SET_SINE	,   \
    CMD_VBIAS_STOP_SINE	,   \
    CMD_REQ_FFT_DATA	,   \
    CMD_RETURN_TIP_HOME	,   \
    CMD_STEPPER_RESET_HOME_POSITION	,   \
    CMD_ABORT	,   \
    CMD_ADC_CAL_MODE	,   \
    CMD_ADC_CAL_LOAD_CURR	,   \
    CMD_ADC_CAL_MEAS_GND	,   \
    CMD_ADC_CAL_MEAS_TEST_CURR	,   \
    CMD_ADC_CAL_STOP	,   \
    CMD_DAC_CAL_MODE_VBIAS	,   \
    CMD_DAC_CAL_MODE_VPZO	,   \
    CMD_DAC_CAL_SET_0V	,   \
    CMD_DAC_CAL_STORE_0V	,   \
    CMD_DAC_CAL_SET_MID_SCALE	,   \
    CMD_DAC_CAL_STORE_MID_SCALE	,   \
    CMD_DAC_CAL_CHECK, \
    CMD_DAC_CAL_STOP = range(0 , 29)

class ztmSTATUS(Enum):
    STATUS_ACK,\
    STATUS_NACK,\
    STATUS_DONE,\
    STATUS_FAIL,\
    STATUS_RESEND,\
    STATUS_OVERCURRENT,\
    STATUS_CLR,\
    STATUS_RDY,\
    STATUS_BUSY,\
    STATUS_ERROR,\
    STATUS_STEP_COUNT,\
    STATUS_MEASUREMENTS,\
    STATUS_FFT_DATA,\
    STATUS_TIP_CRASHED = range(0 , 14)



class usbMsgFunctions:
    def __init__(self, val):
        self.val=val
        
    ################################################
    # STANDARD COMMAND MESSAGES FOR ZTM CONTROLLER #
    ################################################

# MSG A 
    def sendMsgA(self, port, msgCmd, msgStatus, current_nA, vbias, vpzo):
        ''' - port       = COM port variable assigned using pySerial functions
            - msgCmd     = ztmCMD value - see documentation for valid commands
            - msgStatus  = ztmStatus value
            - current_nA = current as float, units of nA
            - vbias      = bias voltage as a float, units of volts
            - vpzo       = piezo voltage as a float, units of volts
            - Function transmits Msg A, returns True if successful, else false. '''
        
        #headerA = [MSG_A, msgCmd, msgStatus]
    #
        #currentBytes = struct.pack('f', current_nA)
        #vbiasBytes = struct.pack('H', ztmConvert.get_Vbias_int(vbias))
        #vpzoBytes = struct.pack('H', ztmConvert.get_Vpiezo_int16(vpzo))

        messageA = struct.pack('<BBBfHH', GLOBALS.MSG_A, msgCmd, msgStatus, current_nA, Convert.get_Vbias_int(vbias), Convert.get_Vpiezo_int(vpzo))
        retry = 0
        maxRetries = 10
        while retry < maxRetries:  
            try:   
                port.write(serial.to_bytes(messageA)) 
                # clear buffer
                port.flush() 
                return True
            except serial.SerialException as e:
                print(f"Write operation failed: {e}")
                retry += 1
        print("Failed to send message.\n")    
        return False 

    # MSG B
    # Note: account for parsing different commands and rateHz vs. sample size
    def sendMsgB(self, port, msgCmd, msgStatus, uint16_rateHz):
        ''' - port          = COM port variable assigned using pySerial functions
            - msgCmd        = ztmCMD value - see documentation for valid commands
            - msgStatus     = ztmStatus value - usually STATUS_CLR
            - uint16_rateHz = data rate to assign, units of Hz, max limit 65535
            - Function transmits Msg B, returns True if successful, else false. '''
        #headerB = [MSG_B, msgCmd, msgStatus]
        #padBytes = padByte * (payloadBytes - 2)

        payload = bytes(GLOBALS.PAYLOAD_BYTES - 2) 
        rateHzBytes = struct.pack('H', uint16_rateHz)
        
        messageB = struct.pack('<BBBHBBBBBB', GLOBALS.MSG_B, msgCmd, msgStatus, uint16_rateHz, *payload)
        retry = 0
        maxRetries = 10
        while retry < maxRetries:  
            try:      
                port.write(serial.to_bytes(messageB)) 
                # clear buffer    
                port.flush()       
                return True
            except serial.SerialException as e:
                print(f"Write operation failed: {e}")
                retry += 1
        print("Failed to send message.\n")    
        return False        

    # MSG C
    def sendMsgC(self, port, msgCmd, msgStatus):
        ''' - port          = COM port variable assigned using pySerial functions
            - msgCmd        = ztmCMD value - see documentation for valid commands
            - msgStatus     = ztmStatus value - usually STATUS_CLR
            - Function transmits Msg C, does not return anything.
            - MSG C is meant solely to send/receive commands and statuses (ex. ACK or DONE)'''    
        
        #headerC = [MSG_C, msgCmd, msgStatus]
        payload = padByte * 8
        messageC = struct.pack('BBBBBBBBBBB', GLOBALS.MSG_C, msgCmd, msgStatus, *payload)
        retry = 0
        maxRetries = 10
        while retry < maxRetries:
            try:   
                port.write(serial.to_bytes(messageC))
                # clear buffer    
                time.sleep(0.001)
                port.flush()  
                return True
            except serial.SerialException as e:
                print(f"Write operation failed: {e}")
                retry += 1
        print("Failed to send message.\n")    
        return False  

    # MSG D
    def sendMsgD(self, port, msgCmd, msgStatus, size, dir, count):
        ''' - port          = COM port variable assigned using pySerial functions
            - msgCmd        = ztmCMD value - see documentation for valid commands
            - msgStatus     = ztmStatus value - usually STATUS_CLR
            - size          = step size - see global constants, ex. FULL_STEP
            - dir           = direction assignment, raise or lower the top plate of microscope
                              ex. DIR_UP (value should be 1 or 0)
            - count         = number of steps at the designated step size
            - Function transmits Msg D, returns True if successful, else false. '''        

        payload = bytes(2)
        messageD = struct.pack('<BBBBBiBB', GLOBALS.MSG_D, msgCmd, msgStatus, size, dir, count, *payload)

        retry = 0
        maxRetries = 10
        while retry < maxRetries:
            try:     
                port.write(serial.to_bytes(messageD))
                ## clear buffer    
                port.flush()   
                return True  
            except serial.SerialException as e:
                print(f"Write operation failed: {e}")
                retry += 1
        print("Failed to send message.\n")    
        return False   

    # MSG E
    # Not needed for GUI
    def sendMsgE(self, port, sineVbiasAmp, uint16_rateHz):
        ''' - port          = COM port variable assigned using pySerial functions
            - uint16_rateHz = vbias frequency, units of Hz, max valid freq = 5000 Hz
            - Function transmits Msg E, does not return anything. '''           
        # ONLY VALID CMD IN MSG E IS CMD_VBIAS_SET_SINE
        headerE = [GLOBALS.MSG_E, ztmCMD.CMD_VBIAS_SET_SINE.value, ztmSTATUS.STATUS_CLR.value]
        sineVbiasBytes = struct.pack('H', Convert.get_Vbias_int(sineVbiasAmp))
        rateHzBytes = struct.pack('H', uint16_rateHz)
        payloadByteLen = GLOBALS.PAYLOAD_BYTES - 4
        payload = bytes(4)
        messageE = struct.pack('<BBBHHBBBB', GLOBALS.MSG_E, ztmCMD.CMD_VBIAS_SET_SINE.value, ztmSTATUS.STATUS_CLR.value, 
                                                Convert.get_Vbias_int(sineVbiasAmp), uint16_rateHz, *payload)

        retry = 0
        maxRetries = 10
        while retry < maxRetries:
            try:    
                port.write(serial.to_bytes(messageE))
                # clear buffer    
                port.flush()
                return True
            except serial.SerialException as e:
                print(f"Write operation failed: {e}")
                retry += 1
        print("Failed to send message.\n")    
        return False    
        
    ###############################################
    # UNPACK MSG DATA - Reading MCU
    def unpackRxMsg(self, rxMsg):
        ################################
        # DEBUG - PRINT CMD AND STATUS #
        try:
            cmdRx = ztmCMD(rxMsg[cmdByte])
            #print("Received : " + cmdRx.name)
            statRx = ztmSTATUS(rxMsg[statByte])
            #print("Received : " + statRx.name + "\n")
   
        ################################
        
        # EXTRACT THE DATA FROM RX MSG #
            if(rxMsg[0] == GLOBALS.MSG_A):
                if(rxMsg[cmdByte] != ztmCMD.CMD_CLR.value):
                    # microcontroller should not send commands
                    return False
                elif(rxMsg[2] == ztmSTATUS.STATUS_MEASUREMENTS.value):              
                    adcRx_nA    = round(struct.unpack('f', bytes(rxMsg[3:7]))[0], 4)                                #unpack bytes & convert  
                    vBiasRx_V   = round(Convert.get_Vbias_float(struct.unpack('H',bytes(rxMsg[7:9]))[0]), 3)   #unpack bytes & convert
                    vPiezoRx_V  = round(Convert.get_Vpiezo_float(struct.unpack('H',bytes(rxMsg[9:11]))[0]), 3) #unpack bytes & convert
                    return adcRx_nA, vBiasRx_V, vPiezoRx_V
                else:
                    return False

            elif (rxMsg[0] == GLOBALS.MSG_B):
                # microcontroller should not send msg B       
                return False

            elif (rxMsg[0] == GLOBALS.MSG_C):
                if(rxMsg[cmdByte] != ztmCMD.CMD_CLR.value):
                    # microcontroller should not send commands
                    return False
                else:
                    statRx = ztmSTATUS(rxMsg[statByte])
                    #print("Received : " + statRx.name + "\n")
                    return rxMsg[statByte]

            elif (rxMsg[0] == GLOBALS.MSG_D):
                if(rxMsg[cmdByte] != ztmCMD.CMD_CLR.value):
                    # microcontroller should not send commands
                    return False
                else:
                    stepsRx = struct.unpack('i', bytes(rxMsg[5:9]))[0]               
                    stepsRx = stepsRx / 8   # return the number of full steps as a float for conversion
                    return stepsRx 

            elif (rxMsg[0] == GLOBALS.MSG_E):
                # microcontroller should not send msg B       
                return False 

            elif (rxMsg[0] == GLOBALS.MSG_F):
                if(rxMsg[cmdByte] != ztmCMD.CMD_CLR.value):
                    # microcontroller should not send commands     
                    return False
                else:
                    adcRxFFT_nA = round(struct.unpack('f', bytes(rxMsg[3:7]))[0], 3) # unpack bytes & convert                                     
                    freqRxFFT_Hz = round(struct.unpack('f', bytes(rxMsg[7:11]))[0], 3) # unpack bytes & convert 
                    return adcRxFFT_nA, freqRxFFT_Hz

        except:
            print("Bytes not yet received.\n")   
            return False  
            
    ###############################################
    # CALIBRATION SCRIPT MESSAGING FUNCTIONS
    ###############################################

    # the calibration script fucntions could probably all be replaced by the above messaging functions that 
    # allows the user to select the msg/cmd/status/payload values, but for simplicity & speed of 
    # development a different function was made for each message used in the cal procedure

    ###########################################
    # -MSG A PAYLOAD-
    # adc curr[0] 
    # adc curr[1]
    # adc curr[2]
    # adc curr[3]
    # vbias[0]
    # vbias[1]
    # vpzo[0]
    # vpzo[1]
    ###########################################

    # ADC COMMS #
    def startAdcCalMode(ztmComms):
        ''' send data byte by byte'''

        MsgId   = GLOBALS.MSG_X
        CmdByte = [ztmCMD.CMD_ADC_CAL_MODE.value]
        #padByte = [0x1]

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)

        for i in range(0, GLOBALS.PAYLOAD_BYTES+1):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)
        # clear buffer    
        ztmComms.flush()

    def sendAdcTestCurrent(ztmComms, testCurrent):
        ''' send data byte by byte'''

        MsgId   = GLOBALS.MSG_X
        CmdByte = [ztmCMD.CMD_ADC_CAL_LOAD_CURR.value]
        #padByte = [0x0]
      
        # extract bytes
        #testCurrBytes = [0, 0, 0]
        #testCurrBytes[0] =  testCurrent & 0x0000FF
        #testCurrBytes[1] = (testCurrent >> 8) & 0x0000FF
        #testCurrBytes[2] = (testCurrent >> 16) & 0x0000FF
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
        # for byte in testCurrBytes:
        #     ztmComms.write(serial.to_bytes([byte]))
        #     time.sleep(usbDelay)
        data_bytes = struct.pack('f', testCurrent)
        # Send bytes over serial
        for byte in data_bytes:
            ztmComms.write(serial.to_bytes([byte]))

        for i in range(0, vByteLen):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)

        # clear buffer    
        ztmComms.flush()

    def adcCalCmd_0V(ztmComms):
        ''' send data byte by byte'''

        MsgId   = GLOBALS.MSG_X
        CmdByte = [ztmCMD.CMD_ADC_CAL_MEAS_GND.value]
        #padByte = [0x0]

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)

        for i in range(0, GLOBALS.PAYLOAD_BYTES+1):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)

        # clear buffer    
        ztmComms.flush()

    def adcCalCmd_TestCurr(ztmComms):
        ''' send data byte by byte'''

        MsgId   = GLOBALS.MSG_X
        CmdByte = [ztmCMD.CMD_ADC_CAL_MEAS_TEST_CURR.value]
        #padByte = [0x0]

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)

        for i in range(0, GLOBALS.PAYLOAD_BYTES+1):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)

        # clear buffer    
        ztmComms.flush()   


    def adcCalCmd_CalStop(ztmComms):
        ''' send data byte by byte'''

        MsgId   = GLOBALS.MSG_X
        CmdByte = [ztmCMD.CMD_ADC_CAL_STOP.value]
        #padByte = [0x0]

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)

        for i in range(0, GLOBALS.PAYLOAD_BYTES+1):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)

        # clear buffer    
        ztmComms.flush() 

    #############
    # DAC COMMS #
    def startDacCalMode(ztmComms, dacSel):
        ''' send data byte by byte'''
        MsgId   = GLOBALS.MSG_X
        if(dacSel == "piezo"):
            CmdByte = [ztmCMD.CMD_DAC_CAL_MODE_VPZO.value]
        else:
            CmdByte = [ztmCMD.CMD_DAC_CAL_MODE_VBIAS.value]    
        #padByte = [0x0]

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)

        for i in range(0, GLOBALS.PAYLOAD_BYTES+1):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)
        # clear buffer    
        ztmComms.flush()  

    def dacCalCmd_0V(ztmComms):
        ''' send data byte by byte'''

        MsgId   = GLOBALS.MSG_X
        CmdByte = [ztmCMD.CMD_DAC_CAL_SET_0V.value]
        #padByte = [0x0]

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)

        for i in range(0, GLOBALS.PAYLOAD_BYTES+1):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)

        # clear buffer    
        ztmComms.flush()  

    def dacCalCmd_5V(ztmComms):
        ''' send data byte by byte'''

        MsgId   = GLOBALS.MSG_X
        CmdByte = [ztmCMD.CMD_DAC_CAL_SET_MID_SCALE.value]
        #padByte = [0x0]

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)

        for i in range(0, GLOBALS.PAYLOAD_BYTES+1):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)

        # clear buffer    
        ztmComms.flush()     

    def dacCalCmd_Check(ztmComms):
        ''' send data byte by byte'''

        MsgId   = GLOBALS.MSG_X
        CmdByte = [ztmCMD.CMD_DAC_CAL_CHECK.value]
        #padByte = [0x0]

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)

        for i in range(0, GLOBALS.PAYLOAD_BYTES+1):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)

        # clear buffer    
        ztmComms.flush()  

    def dacCalCmd_CalStop(ztmComms):
        ''' send data byte by byte'''

        MsgId   = GLOBALS.MSG_X
        CmdByte = [ztmCMD.CMD_DAC_CAL_STOP.value]
        #padByte = [0x0]

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)

        for i in range(0, GLOBALS.PAYLOAD_BYTES+1):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)

        # clear buffer    
        ztmComms.flush() 

    def sendDacMeasurement0v(ztmComms, dacSel, dacMeas):
        ''' send data byte by byte'''

        vbiasBytes = [0x00, 0x00]
        vpzoBytes  = [0x00, 0x00]

        MsgId   = GLOBALS.MSG_X
        CmdByte = [ztmCMD.CMD_DAC_CAL_STORE_0V.value]
        #padByte = [0x0]    

        # extract bytes from measurement
        dacMeasBytes = [0, 0]
        dacMeasBytes[0] =  dacMeas & 0x0000FF
        dacMeasBytes[1] = (dacMeas >> 8) & 0x0000FF

        #debug
            # Print each element of testCurrBytes in hexadecimal format
        print([hex(byte) for byte in dacMeasBytes])

        if(dacSel == "piezo"):
            vpzoBytes = dacMeasBytes
        else:
            vbiasBytes = dacMeasBytes

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)
        # send empty Status
        ztmComms.write(serial.to_bytes(padByte))
        time.sleep(usbDelay)  

        #send empty current bytes
        for i in range(0, adcByteLen):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)

        #send vbias
        for byte in vbiasBytes:
            ztmComms.write(serial.to_bytes([byte]))
            time.sleep(usbDelay)

        #send vpzo
        for byte in vpzoBytes:
            ztmComms.write(serial.to_bytes([byte]))
            time.sleep(usbDelay)

        # clear buffer    
        ztmComms.flush()    

    def sendDacMeasurement5v(ztmComms, dacSel, dacMeas):
        ''' send data byte by byte'''

        vbiasBytes = [0x00, 0x00]
        vpzoBytes  = [0x00, 0x00]

        MsgId   = GLOBALS.MSG_X
        CmdByte = [ztmCMD.CMD_DAC_CAL_STORE_MID_SCALE.value]
        #padByte = [0x0]    

        # extract bytes from measurement
        dacMeasBytes = [0, 0]
        dacMeasBytes[0] =  dacMeas & 0x0000FF
        dacMeasBytes[1] = (dacMeas >> 8) & 0x0000FF

        #debug
            # Print each element of testCurrBytes in hexadecimal format
        print([hex(byte) for byte in dacMeasBytes])

        if(dacSel == "piezo"):
            vpzoBytes = dacMeasBytes
        else:
            vbiasBytes = dacMeasBytes

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)
        # send empty Status
        ztmComms.write(serial.to_bytes(padByte))
        time.sleep(usbDelay)  

        #send empty current bytes
        for i in range(0, adcByteLen):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)

        #send vbias
        for byte in vbiasBytes:
            ztmComms.write(serial.to_bytes([byte]))
            time.sleep(usbDelay)

        #send vpzo
        for byte in vpzoBytes:
            ztmComms.write(serial.to_bytes([byte]))
            time.sleep(usbDelay)

        # clear buffer    
        ztmComms.flush()

    def dacCalStatus(ztmComms, status):
        ''' send data byte by byte'''

        MsgId   = GLOBALS.MSG_X
        CmdByte = [ztmCMD.CMD_CLR.value]
        StatByte = [status]
        #padByte = [0x0]

        # send ID
        ztmComms.write(serial.to_bytes(MsgId))
        time.sleep(usbDelay)
        # send CMD
        ztmComms.write(serial.to_bytes(CmdByte))
        time.sleep(usbDelay)
        # send STATUS
        ztmComms.write(serial.to_bytes(StatByte))
        time.sleep(usbDelay)


        for i in range(0, GLOBALS.PAYLOAD_BYTES):
            ztmComms.write(serial.to_bytes(padByte))
            time.sleep(usbDelay)

        # clear buffer    
        ztmComms.flush()             