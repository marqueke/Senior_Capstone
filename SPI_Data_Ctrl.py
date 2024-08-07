import serial
import threading
import time
import globals

class SerialCtrl:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        #self.callback = callback
        self.serial_port = None
        self.thread = None
        self.running = False
        self.buffer = bytearray()

    
    # used to continuously read data from port
    # useful for data acquisition and background processing
    def read_serial(self):
        while self.running and self.serial_port:
            try:
                if self.serial_port.in_waiting > 0:
                    raw_data = self.serial_port.read(self.serial_port.in_waiting)
                    self.buffer.extend(raw_data)
                    
                    # Process complete frames (11 bytes each)
                    while len(self.buffer) >= globals.MSG_BYTES:
                        frame = self.buffer[:globals.MSG_BYTES]
                        self.buffer = self.buffer[globals.MSG_BYTES:]
                    return raw_data
            except serial.SerialException as e:
                print(f"Error reading serial port: {e}")
                self.running = False
    
    
    '''
    # Blocking read method- reads specified 11 bytes from port
    # useful for waiting for a specific response from MCU immediately after
    # sending a command
    def read_serial_blocking(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                raw_data = self.serial_port.read(globals.MSG_BYTES)  # Read 11 bytes blocking
                if raw_data:
                    print(f"Received data: {raw_data.hex()}")
                    return raw_data
                else:
                    print("No data received.")
                    return None
            except serial.SerialException as e:
                print(f"Failed to read from serial port: {e}")
                return None
        else:
            print("Serial port is not open. Call start() first.")
            return None
    '''

    
    def ztmGetMsg(self, port):
        ''' Attempt to read a message from the ZTM controller'''
        
        attempts = 0
        response = b''  # Initialize an empty byte string to store the response
        while(attempts < globals.MAX_ATTEMPTS):
            try:
                response = port.read(globals.MSG_BYTES)
                return response
            except serial.SerialException as e:
                print(f"Read operation failed: {e}")    
                attempts += 1        
        if attempts == globals.MAX_ATTEMPTS:
            print(f"Failed to receive complete message.\n")   
            return False
    

    '''
    # function to read msg of 11 bytes
    def read_bytes(self):
        count = 0
        response = None

        while count < GLOBALS.MAX_ATTEMPTS:
            if self.serial_port and self.serial_port.is_open:
                try:
                    # Attempt to read 11 bytes with a timeout
                    response = self.serial_port.read(GLOBALS.MSG_BYTES)
                    if response and len(response) == GLOBALS.MSG_BYTES:
                        if response[0] not in [GLOBALS.MSG_A, GLOBALS.MSG_B, GLOBALS.MSG_C, GLOBALS.MSG_D, GLOBALS.MSG_E]:
                            print("Message received out of order.\n")
                            return None
                        else:
                            print(f"\nMCU Response (raw bytes):", response.hex())
                            return response
                    else:
                        print("No response received from MCU, retrying...")
                        count += 1
                        time.sleep(GLOBALS.ONE_SECOND)
                        return None
                except serial.SerialTimeoutException:
                    print("Read timed out, retrying...")
                    count += 1
                    time.sleep(GLOBALS.ONE_SECOND)
                    return None
            else:
                print("Serial port is not open.")
                return None
        if not response:
            print("Failed to receive response from MCU after multiple attempts.")
            return None
    '''    
                
    # WRITE FUNCTION TO SEND DATA BACK TO MCU
    def write_serial(self, data):
        if self.serial_port:
            try:
                byte_data = bytearray(data)  # Convert list to bytearray
                self.serial_port.write(byte_data)
                print(f"Sent data: {byte_data.hex()}")
            except serial.SerialException as e:
                print(f"Failed to write to serial port: {e}")
        else:
            print("Serial port is not open. Call start() first.")
    
    def start(self):
        if not self.running:
            try:
                self.serial_port = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=2,  # Set a timeout for read operations
                    write_timeout=2,  # Set a timeout for write operations
                    xonxoff=True,
                )
                self.running = True
                self.thread = threading.Thread(target=self.read_serial)
                self.thread.start()
                print("Reading thread started.")
                
                return True
            except serial.SerialException as e:
                print(f"Error opening serial port: {e}")
                self.serial_port = None
                
                return False

    def stop(self):
        self.running = False
        if self.serial_port:
            self.thread.join()
            self.serial_port.close()