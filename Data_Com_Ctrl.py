import struct
from value_conversion import Convert
from ztmSerialCommLibrary import ztmCMD, ztmSTATUS, usbMsgFunctions, MSG_A, MSG_E, MSG_F

class DataCtrl:
    def __init__(self, baudrate):
        self.baudrate = baudrate
        
    def decode_data(self, raw_data):
        try:
            # Ensure raw_data is bytes
            if isinstance(raw_data, str):
                raw_data = raw_data.encode('utf-8')
            print(f"Raw data: {raw_data}")  # Debugging print statement
            header = struct.unpack('BBB', raw_data[:3])
            msg, cmd, status = header
            payload = raw_data[3:]

            print(f"Header - MSG: {msg}, CMD: {cmd}, STATUS: {status}")
            print(f"Payload: {payload}")

            if msg == MSG_A and cmd == ztmCMD.CMD_CLR.value and status == ztmSTATUS.STATUS_CLR.value:
                adc_curr = (payload[0] << 16) | (payload[1] << 8) | payload[2]
                vbias = (payload[3] << 8) | (payload[4])
                vpzo = (payload[5] << 8) | (payload[6])

                adc_curr_float = Convert.get_curr_float(adc_curr)
                vbias_float = Convert.get_Vbias_float(vbias)
                vpzo_float = Convert.get_Vpiezo_float(vpzo)

                data_string = f"ADC_CURR: {adc_curr_float:.3f} nA, VBIAS: {vbias_float:.3f} V, VPZO: {vpzo_float:.3f} V"
                print(data_string)  # Debugging print statement
                self.callback(data_string)  # Pass the full string to the callback
            else:
                print(f"Unhandled MSG ID: {msg}")
        except Exception as e:
            print(f"Error handling data: {e}")

    
    def send_command(self, ztmComms, cmd, payload=[]):
        usbMsgFunctions.send_command(ztmComms, MSG_A, cmd, payload)
        