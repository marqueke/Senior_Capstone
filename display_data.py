from ztmSerialCommLibrary import usbMsgFunctions, MSG_A, ztmCMD, ztmSTATUS
from value_conversion import Convert
import struct

###########################################################################
# EXAMPLE OF LOADING AND DECODING MESSAGE A

    # start with an empty dummy message
testMsg = [MSG_A, ztmCMD.CMD_CLR.value, ztmSTATUS.STATUS_MEASUREMENTS.value, 0X00, 0X00, 0X00, 0X00, 0x00, 0x00, 0x00, 0x00] 
    # values of interest
testCurrent = 2.547895322   # Example float value to pack into bytes
vB = 4.5                    # example vbias V from gui
vP = 6.7                    # example vpiezo V from gui

# Pack the floats into bytes objects
testCurrBytes = struct.pack('f', testCurrent)
vbiasBytes = struct.pack('H', Convert.get_Vbias_int(vB))
vpzoBytes = struct.pack('H', Convert.get_Vpiezo_int(vP))

print(f"{testCurrBytes.hex()}")
print(f"{vbiasBytes.hex()}")
print(f"{vpzoBytes.hex()}")

# load them into the dummy message
testMsg[3:7]  = list(testCurrBytes)
testMsg[7:9]  = list(vbiasBytes)
testMsg[9:11] = list(vpzoBytes)

# Pretend we received the message - we need to decode the data for use/display
    # current
current_nA = round(struct.unpack('f', bytes(testMsg[3:7]))[0], 3) #unpack bytes & convert
cStr = str(current_nA)  # format as a string
print("Received values\n\tCurrent: " + cStr + " nA\n")
    
vb_V = round(Convert.get_Vbias_float(struct.unpack('H',bytes(testMsg[7:9]))[0]), 3) #unpack bytes & convert
vbStr = str(vb_V)   # format as a string
print("\tVbias: " + vbStr + " V\n")
    # vpiezo
vp_V = round(Convert.get_Vpiezo_float(struct.unpack('H',bytes(testMsg[9:11]))[0]), 3) #unpack bytes & convert
vpStr = str(vp_V)   # format as a string
print("\tVpiezo: " + vpStr + " V\n")

# if we want to decode the command or status & print to the console....
cmdRx = ztmCMD(testMsg[1])
print("Received : " + cmdRx.name)
statRx = ztmSTATUS(testMsg[2])
print("Received : " + statRx.name + "\n")



###########################################################################