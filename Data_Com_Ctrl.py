import GLOBALS

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
        if len(raw_data) < GLOBALS.MSG_BYTES:
            print("Incomplete data frame received.")
            return None

    '''
    def send_command(self, msg, cmd, status, payload):
        data = struct.pack('BBB', msg, cmd, status) + payload
        print(f"Sending command: {data.hex()}")
        self.serial_ctrl.write_serial(data) 
    '''
        