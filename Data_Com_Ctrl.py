import struct
from value_conversion import Convert
from ztmSerialCommLibrary import ztmCMD, ztmSTATUS, usbMsgFunctions

class DataCtrl:
    def __init__(self, callback):
        self.callback = callback
    
    def decode_data(self, raw_data):
        # Decode based on message structure
        if len(raw_data) < 10:
            print("Incomplete data frame received.")
            return None
        
        header = struct.unpack('BBB', raw_data[:3])
        payload = raw_data[3:]
        
        msg = header[0]
        cmd = header[1]
        status = header[2]
        
        print(f"Decoded Header: MSG={msg}, CMD={cmd}, STATUS={status}")
        
        # Will be testing with 0x0A, 0x00, 0x06, ADC current data
        # Message sends Msg!, CMD_CLEAR, STATUS_CLR, payload loaded with data
        if msg == 0x0A and cmd == ztmCMD.CMD_CLR and status == ztmSTATUS.STATUS_CLR:
            adc_curr = (payload[0] << 16) | (payload[1] << 8) | payload[2]
            vbias = (payload[3] << 8) | (payload[4])
            vpzo = (payload[5] << 8) | (payload[6])
            
            adc_curr_float = Convert.get_curr_float(adc_curr)
            vbias_float = Convert.get_Vbias_float(vbias)
            vpzo_float = Convert.get_Vpiezo_float(vpzo)
            
            return f"ADC_CURR: {adc_curr_float:.3f} nA, VBIAS: {vbias_float:.3f} V, VPZO: {vpzo_float:0.3f} V"
            
        return None
    
    def send_command(self, ztmComms, cmd, payload=[]):
        usbMsgFunctions.send_command(ztmComms, MSG_A, cmd, payload)
        