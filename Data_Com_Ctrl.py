import struct
from value_conversion import Convert
from ztmSerialCommLibrary import ztmCMD, ztmSTATUS, usbMsgFunctions, MSG_A, MSG_B, MSG_C, MSG_D, MSG_E, MSG_F

from SPI_Data_Ctrl import SerialCtrl
'''
MSG A used to set voltage outputs and transmit standard measurements
MSG B used for data and sampling rates
MSG C used for CMDs and STATUSes
MSG D used by PC to command the MCU to step the stepper motor at a defined step size
        - used by MCU to transmit total # of stepper motor steps (in 1/8 steps)
MSG E used by PC to CMD the MCU to set a sinusoidal vbias
MSG F used by MCU to transmit FFT results - amplitude and frequency
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

    def set_serial_ctrl(self, serial_ctrl):
        self.serial_ctrl = serial_ctrl
        
    def decode_data(self, raw_data):
        """
        Decodes the received raw data into meaningful values.
        
        :param raw_data: The raw data received from the serial port.
        :return: Decoded data or None if the frame is incomplete.
        """
        #print(f"Raw data received (length {len(raw_data)}): {raw_data.hex()}")
        if len(raw_data) < 11:
            print("Incomplete data frame received.")
            return None

        msg = raw_data[0]
        cmd = raw_data[1]
        status = raw_data[2]
        payload = raw_data[3:11]

        #print(f"Decoded Header: MSG={msg}, CMD={cmd}, STATUS={status}, PAYLOAD={payload}")

    def send_command(self, msg, cmd, status, payload):
        data = struct.pack('BBB', msg, cmd, status) + payload
        print(f"Sending command: {data.hex()}")
        self.serial_ctrl.write_serial(data) 

    ##### MESSAGE B #####
    def handle_msg_b(self, cmd, status, payload):
        print("**********Handling MSG_B**********")
        
        
        # Need to send msg to MCU that we have entered I-Z mode
        # Need to send start/stop Vpzo seep
        # Need to display current, piezo voltage, delta z
        # Abort CMD
        if cmd == ztmCMD.CMD_CLR.value and status == ztmSTATUS.STATUS_CLR.value:
            baud_rate = (payload[0] << 8) | payload[1]
            empty_byte = (payload[2] << 40) | (payload[3] << 32) | (payload[4] << 24) | (payload[5] << 16) | (payload[6] << 8) | payload[7]               


            print(f"BAUD RATE: {baud_rate: } Hz")
            
            return baud_rate
        else:
            print("Unhandled CMD or STATUS for MSG_B")
            return None
        
'''
        ####################################################### THIS WILL BE THE "STATE MACHINE" #######################################################
        # read and write to MCU
        if msg == MSG_A:
            return self.handle_msg_a(cmd, status, payload)
        # write IZ to MCU
        elif msg == MSG_B:
            return self.handle_msg_b(cmd, status, payload)
        # write IV to MCU
        elif msg == MSG_C:
            return self.handle_msg_c(cmd, status, payload)
        # write to MCU
        elif msg == MSG_D:
            return self.handle_msg_d(cmd, status, payload)
        # no payload
        elif msg == MSG_E:
            return self.handle_msg_e(cmd, status, payload)
        elif msg == MSG_F:
            return self.handle_msg_f(cmd, status, payload)
        else:
            print("Unknown message type received.")
            return None
    
    
    ##### MESSAGE A #####
    def handle_msg_a(self, cmd, status, payload):
        print("**********Handling MSG_A**********")
        
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
            
            self.callback(adc_curr_float, vbias_float, vpzo_float)
            return adc_curr_float, vbias_float, vpzo_float
        
        # write vbias and vpiezo to MCU
        elif cmd == ztmCMD.CMD_SET_VBIAS.value:
            vbias = (payload[4] << 8) | payload[5]
            print(f"Setting VBIAS to: {vbias}")
            self.send_command(MSG_A, ztmCMD.CMD_SET_VBIAS.value, ztmSTATUS.STATUS_CLR.value, vbias)
        
        elif cmd == ztmCMD.CMD_PIEZO_ADJ.value:
            vpzo = (payload[6] << 8) | payload[7]
            print(f"Setting VPIEZO to: {vbias}")
            self.send_command(MSG_A, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_CLR.value, vpzo)
            
        else:
            print("Unhandled CMD or STATUS for MSG_A")
            return None

    ##### MESSAGE B #####
    def handle_msg_b(self, cmd, status, payload):
        print("**********Handling MSG_B**********")
        
        
        # Need to send msg to MCU that we have entered I-Z mode
        # Need to send start/stop Vpzo seep
        # Need to display current, piezo voltage, delta z
        # Abort CMD
        if cmd == ztmCMD.CMD_CLR.value and status == ztmSTATUS.STATUS_CLR.value:
            baud_rate = (payload[0] << 8) | payload[1]
            empty_byte = (payload[2] << 40) | (payload[3] << 32) | (payload[4] << 24) | (payload[5] << 16) | (payload[6] << 8) | payload[7]               


            print(f"BAUD RATE: {baud_rate: } Hz")
            
            return baud_rate
        else:
            print("Unhandled CMD or STATUS for MSG_B")
            return None

    
    ##### MESSAGE C #####
    def handle_msg_c(self, cmd, status, payload):
        print("**********Handling MSG_C**********")
        
        if status == ztmSTATUS.STATUS_CLR.value:
            if cmd == ztmCMD.CMD_REQ_DATA.value:
                print(f"MSG C: Disabled data.")
            elif cmd == ztmCMD.CMD_REQ_STEP_COUNT.value:
                print(f"MSG C: Request step count.")
            elif cmd == ztmCMD.CMD_SCOPE_START.value:
                print(f"MSG C: Start seeking tunneling current.")
            elif cmd == ztmCMD.CMD_VBIAS_STOP_SINE.value:
                print(f"MSG C: Set sinusoidal Vbias stop value.")
            elif cmd == ztmCMD.CMD_REQ_FFT_DATA.value:
                print(f"MSG C: Request FFT data.")
            elif cmd == ztmCMD.CMD_RETURN_TIP_HOME.value:
                print(f"MSG C: Return tip to home position.")
            elif cmd == ztmCMD.CMD_STEPPER_RESET_HOME_POSITION.value:
                print(f"MSG C: Reset the stepper home position.")
            elif cmd == ztmCMD.CMD_ABORT.value:
                print(f"MSG C: Abort operation.")
        elif cmd == ztmCMD.CMD_CLR.value:
            if status == ztmSTATUS.STATUS_ACK.value:
                print(f"MSG C: ACK")
            elif status == ztmSTATUS.STATUS_NACK.value:
                print(f"MSG C: NACK")
            elif status == ztmSTATUS.STATUS_DONE.value:
                print(f"MSG C: DONE")
            elif status == ztmSTATUS.STATUS_FAIL.value:
                print(f"MSG C: FAIL")
            elif status == ztmSTATUS.STATUS_RESEND.value:
                print(f"MSG C: RESEND")
            elif status == ztmSTATUS.STATUS_CLR.value:
                print(f"MSG C: CLR")
            elif status == ztmSTATUS.STATUS_RDY.value:
                print(f"MSG C: RDY")
            elif status == ztmSTATUS.STATUS_BUSY.value:
                print(f"MSG C: BUSY")
            elif status == ztmSTATUS.STATUS_ERROR.value:
                print(f"MSG C: ERROR")
        else:
            print("Unhandled CMD or STATUS for MSG_C")
            return None

    ##### MESSAGE D #####
    def handle_msg_d(self, cmd, status, payload):
        print("**********Handling MSG_D**********")
        
        # Implement specific handling for MSG_D
        # Need to send sampling rate to MCU across homepage, I-Z, I-V mode
        if cmd == ztmCMD.CMD_CLR.value and status == ztmSTATUS.STATUS_CLR.value:
            step_size = payload[0]
            dir = payload[1]
            num_steps = (payload[2] << 24) | (payload[3] << 16) | (payload[4] << 8) | payload[5]   
            empty = (payload[6] << 8) | payload[7]           

            print(f"STEP SIZE: {step_size}, DIRECTION: {dir}, # OF STEPS: {num_steps}")
            
            return step_size, dir, num_steps
        else:
            print("Unhandled CMD or STATUS for MSG_D")


    ##### MESSAGE E #####
    def handle_msg_e(self, cmd, status, payload):
        print("**********Handling MSG_E**********")
    
        
        if cmd == ztmCMD.CMD_VBIAS_SET_SINE.value and status == ztmSTATUS.STATUS_CLR.value:
            vbias_sine_amp = (payload[0] << 8) | payload[1]
            freq = (payload[2] << 8) | payload[3]
            empty = (payload[4] << 24) | (payload[5] << 16) | (payload[6] << 8) | payload[7]
            
            print(f"VBIAS SINE AMPLITUDE: {vbias_sine_amp}, FREQUENCY: {freq} Hz")
            return vbias_sine_amp, freq
        else:
            print("Unhandled CMD or STATUS for MSG_E")
        
    ##### MESSAGE F #####
    def handle_msg_f(self, cmd, status, payload):
        print("**********Handling MSG_F**********")

        if cmd == ztmCMD.CMD_CLR.value and status == ztmSTATUS.STATUS_FFT_DATA.value:
            fft_curr_amp = (payload[0] << 24) | (payload[1] << 16) | (payload[2] << 8) | payload[3]
            fft_freq = (payload[4] << 24) | (payload[5] << 16) | (payload[6] << 8) | payload[7]
            
            print(f"FFT CURRENT AMPLITUDE: {fft_curr_amp} nA, FFT FREQUENCY: {fft_freq} Hz")
            return fft_curr_amp, fft_freq
        else:
            print("Unhandled CMD or STATUS for MSG_F")
'''       

