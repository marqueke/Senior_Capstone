'''
# THIS FILE IS INACTIVE

import globals


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