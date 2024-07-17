import struct
from value_conversion import Convert
from ztmSerialCommLibrary import ztmCMD, ztmSTATUS, usbMsgFunctions, MSG_A, MSG_B, MSG_C, MSG_D, MSG_E

'''
MSG A used mainly by MCU to constantly transmit analog levels to PC
    .....can also be used with commands by PC to tell MCU to set levels
    Ex. PC sends msg A with current setpoint command, fills ADC current slot of the payload with desired tunneling current.
MSG B used by PC to set IZ parameters
MSG C used by PC to set IV parameters
MSG D used by PC to set sample rate
MSG E is used to transmit standalone commands or statuses that do not require data in the payload
'''

class DataCtrl:
    def __init__(self, baudrate, callback):
        self.baudrate = baudrate
        self.callback = callback

    def decode_data(self, raw_data):
        print(f"Raw data received (length {len(raw_data)}): {raw_data.hex()}")
        if len(raw_data) < 10:
            print("Incomplete data frame received.")
            return None

        header = struct.unpack('BBB', raw_data[:3])
        payload = struct.unpack('BBBBBBB', raw_data[3:])

        msg = header[0]
        cmd = header[1]
        status = header[2]

        print(f"Decoded Header: MSG={msg}, CMD={cmd}, STATUS={status}")

        ########## THIS WILL BE THE "STATE MACHINE" ##########
        if msg == MSG_A:
            return self.handle_msg_a(cmd, status, payload)
        elif msg == MSG_B:
            return self.handle_msg_b(cmd, status, payload)
        elif msg == MSG_C:
            return self.handle_msg_c(cmd, status, payload)
        elif msg == MSG_D:
            return self.handle_msg_d(cmd, status, payload)
        elif msg == MSG_E:
            return self.handle_msg_e(cmd, status, payload)
        else:
            print("Unknown message type received.")
            return None
    
        
    def handle_msg_a(self, cmd, status, payload):
        print("Handling MSG_A")
        
        '''
        if payload == 0:
            return self.handle_msg_e(cmd, status, payload)
        '''
        # write data to GUI
        # set Vbias
        # set desired ADC current
        # set vpiezo
        
        # read data to GUI
        if cmd == ztmCMD.CMD_CLR.value and status == ztmSTATUS.STATUS_CLR.value:
            adc_curr = (payload[0] << 16) | (payload[1] << 8) | payload[2]
            vbias = (payload[3] << 8) | payload[4]
            vpzo = (payload[5] << 8) | payload[6]

            adc_curr_float = Convert.get_curr_float(adc_curr)
            vbias_float = Convert.get_Vbias_float(vbias)
            vpzo_float = Convert.get_Vpiezo_float(vpzo)

            print(f"ADC_CURR: {adc_curr_float:.3f} nA, VBIAS: {vbias_float:.3f} V, VPZO: {vpzo_float:0.3f} V")
            
            return adc_curr_float, vbias_float, vpzo_float
        else:
            print("Unhandled CMD or STATUS for MSG_A")
            return None

    ##### IZ COMMANDS #####
    def handle_msg_b(self, cmd, status, payload):
        print("Handling MSG_B")
        
        '''
        if payload == 0:
            return self.handle_msg_e(cmd, status, payload)
        '''
        
        # Need to send msg to MCU that we have entered I-Z mode
        # Need to send start/stop Vpzo seep
        # Need to display current, piezo voltage, delta z
        # Abort CMD
        if cmd == ztmCMD.CMD_CLR.value and status == ztmSTATUS.STATUS_CLR.value:
            delta_z = (payload[0] << 24) | (payload[1] << 16) | (payload[2] << 8) | payload[3]
            num_pts = payload[4]
            sample_rate = payload[5]
            empty_byte = payload[6]               


            print(f"DELTA Z: {delta_z:.3f} nA, NUMBER OF POINTS: {num_pts:.3f}, SAMPLE RATE: {sample_rate:0.3f} kHz")
            
            return delta_z, num_pts, sample_rate
        else:
            print("Unhandled CMD or STATUS for MSG_B")
            return None

    ##### IV COMMANDS #####
    def handle_msg_c(self, cmd, status, payload):
        print("Handling MSG_C")
        
        '''
        if payload == 0:
            return self.handle_msg_e(cmd, status, payload)
        '''
        
        # Implement specific handling for MSG_C
        # Need to send msg to MCU that we have entered I-V mode
        # Need to start/stop Vbias sweep
        # Need to display current, vbias
        if cmd == ztmCMD.CMD_CLR.value and status == ztmSTATUS.STATUS_CLR.value:
            start_v = (payload[0] << 8) | payload[1]
            stop_v = (payload[2] << 8) | payload[3]
            num_pts = payload[4]
            sample_rate = payload[5]
            empty_byte = payload[6]               


            print(f"START VOLTAGE: {start_v:.3f} V, STOP VOLTAGE: {stop_v:.3f}, NUMBER OF POINTS: {num_pts:0.3f}, SAMPLE RATE: {sample_rate} kHz")
            
            return start_v, stop_v, num_pts, sample_rate
        else:
            print("Unhandled CMD or STATUS for MSG_C")
            return None

    ##### SAMPLE RATE #####
    def handle_msg_d(self, cmd, status, payload):
        print("Handling MSG_D")
        
        '''
        if payload == 0:
            return self.handle_msg_e(cmd, status, payload)
        '''
        
        # Implement specific handling for MSG_D
        # Need to send sampling rate to MCU across homepage, I-Z, I-V mode
        if cmd == ztmCMD.CMD_CLR.value and status == ztmSTATUS.STATUS_CLR.value:
            sample_rate = payload[0]
            empty_bytes = (payload[1] << 32) | (payload[2] << 24) | (payload[3] << 16) | (payload[4] << 8) | payload[5]               

            print(f"SAMPLE RATE: {sample_rate} kHz")
            
            return sample_rate
        else:
            print("Unhandled CMD or STATUS for MSG_D")
            return None
        return None

    ##### STANDALONE CMD/STATUS, NO DATA #####
    # most likely will be used just for writing to MCU
    def handle_msg_e(self, cmd, status, payload):
        print("Handling MSG_E")
    
        '''
        if payload == 0:
            return self.handle_msg_e(cmd, status, payload)
        '''
        
        # Implement specific handling for MSG_E
        # start seeking current, stop seeking current
        # retract tip, fine adjust
        # acquire iz, iv
        # piezo sweep, bias sweep
        # stop vbias, stop piezo
        # abort
        # STATUS_MSGs
        if cmd == ztmCMD.CMD_CLR:
            if status == ztmSTATUS.STATUS_ACK:
                pass
            elif status == ztmSTATUS.STATUS_NACK:
                pass
            
        return None


    '''
    def send_command(self, ztmComms, cmd, payload=[]):
        usbMsgFunctions.send_command(ztmComms, MSG_A, cmd, payload)
    '''    
        