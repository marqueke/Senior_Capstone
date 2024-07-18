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
        """
        Initializes the DataCtrl class with the specified baudrate and callback function.
        
        :param baudrate: The baud rate for the serial communication.
        :param callback: The callback function to handle decoded data.
        """
        self.baudrate = baudrate
        self.callback = callback
        self.serial_ctrl = None

    def decode_data(self, raw_data):
        """
        Decodes the received raw data into meaningful values.
        
        :param raw_data: The raw data received from the serial port.
        :return: Decoded data or None if the frame is incomplete.
        """
        print(f"Raw data received (length {len(raw_data)}): {raw_data.hex()}")
        if len(raw_data) < 11:
            print("Incomplete data frame received.")
            return None

        header = struct.unpack('BBB', raw_data[:3])
        payload = struct.unpack('BBBBBBBB', raw_data[3:])

        msg = header[0]
        cmd = header[1]
        status = header[2]

        print(f"Decoded Header: MSG={msg}, CMD={cmd}, STATUS={status}")

        ####################################################### THIS WILL BE THE "STATE MACHINE" #######################################################
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
        elif msg == MSG_D:
            return self.handle_msg_g(cmd, status, payload)
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
            adc_curr = (payload[0] << 24) | (payload[1] << 16) | (payload[2] << 8) | payload[3]
            vbias = (payload[4] << 8) | payload[5]
            vpzo = (payload[6] << 8) | payload[7]

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
            empty_byte = (payload[5] << 16) | (payload[6] << 8) | payload[7]               


            print(f"DELTA Z: {delta_z:.3f} nA, NUMBER OF POINTS: {num_pts:.3f}")
            
            return delta_z, num_pts
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
            empty_byte = (payload[5] << 16) | (payload[6] << 8) | payload[7]                


            print(f"START VOLTAGE: {start_v:.3f} V, STOP VOLTAGE: {stop_v:.3f}, NUMBER OF POINTS: {num_pts:0.3f}")
            
            return start_v, stop_v, num_pts
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
            empty_bytes = (payload[1] << 48) | (payload[2] << 40) | (payload[3] << 32) | (payload[4] << 24) | (payload[5] << 16) | (payload[6] << 8) | payload[7]              

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
        if cmd == ztmCMD.CMD_CLR.value:
            if status == ztmSTATUS.STATUS_ACK.value:
                self.send_status_ack()     
            elif status == ztmSTATUS.STATUS_NACK:
                pass
            
        return None

    ##### DELTA Z FOR MOVING TIP AND ADC CURR #####
    # most likely will be used just for writing to MCU
    def handle_msg_g(self, cmd, status, payload):
        print("Handling MSG_G")
    
        '''
        if payload == 0:
            return self.handle_msg_e(cmd, status, payload)
        '''
        
        # Implement specific handling for MSG_G
        # command up or down to move tip
        # retrieving current/distance sent by MCU
        if cmd == ztmCMD.CMD_CLR.value and status == ztmSTATUS.STATUS_CLR.value:
            delta_z = (payload[0] << 24) | (payload[1] << 16) | (payload[2] << 8) | payload[3]
            adc_curr = (payload[4] << 24) | (payload[5] << 16) | (payload[6] << 8) | payload[7]            

            print(f"Delta Z: {delta_z} nm, ADC Current: {adc_curr} nA")
            
            return delta_z, adc_curr
        else:
            print("Unhandled CMD or STATUS for MSG_G")
        return None
    
    ####################################################### COMMANDS #######################################################
    
    def send_command(self, cmd, current_setpoint=0, vbias=0, sample_rate=0):
        """
        Sends a command to the MCU with the appropriate payload.

        Args:
            cmd (ztmCMD): Command to send.
            current_setpoint (int): Current setpoint value in nA (4 bytes).
            vbias (int): Bias voltage value in V (2 bytes).
            sample_rate (int): Sample rate value in kHz (1 byte).
        """
        if cmd == ztmCMD.CMD_CURR_SETPT.value:
            payload = struct.pack('>I', current_setpoint) + b'\x00\x00\x00\x00'
        elif cmd == ztmCMD.CMD_VBIAS_SET.value:
            payload = b'\x00\x00\x00\x00' + struct.pack('>H', vbias) + b'\x00\x00'
        elif cmd == ztmCMD.CMD_SET_SAMPLE_RATE.value:
            payload = b'\x00\x00\x00\x00\x00\x00' + struct.pack('>B', sample_rate) + b'\x00'
        else:
            payload = b'\x00' * 8

        data = struct.pack('BBB', MSG_A, cmd.value, ztmSTATUS.STATUS_CLR.value) + payload
        self.serial_ctrl.write_data(data)

    def send_status(self, status):
        """
        Sends a status message to the MCU.

        Args:
            status (ztmSTATUS): Status to send.
        """
        data = struct.pack('BBB', MSG_E, 0, status.value) + b'\x00' * 8
        self.serial_ctrl.write_bytes(data)
        
    def handle_status_rdy(self):
        self.send_status(ztmSTATUS.STATUS_ACK.value)

    def set_current_setpoint(self, current_setpoint):
        self.send_command(ztmCMD.CMD_CURR_SETPT.value, current_setpoint=current_setpoint)

    def set_vbias(self, vbias):
        self.send_command(ztmCMD.CMD_VBIAS_SET.value, vbias=vbias)

    def set_sample_rate(self, sample_rate):
        self.send_command(ztmCMD.CMD_SET_SAMPLE_RATE.value, sample_rate=sample_rate)

    def process_startup_routine(self):
        self.handle_status_rdy()
        self.set_current_setpoint()  
        self.set_vbias()  
        self.set_sample_rate()  
    
    def set_adjust_up(self, distance):
        pass
    
    def set_adjust_down(self, distance):
        pass
        
            
    '''
    def send_command(self, ztmComms, cmd, payload=[]):
        usbMsgFunctions.send_command(ztmComms, MSG_A, cmd, payload)
    '''    
        