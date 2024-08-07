import serial
import threading
import queue
import globals

class SerialCtrl:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.serial_port = None
        self.send_thread = None
        self.receive_thread = None
        self.send_queue = queue.Queue()  # Queue for data to be sent
        self.receive_queue = queue.Queue()  # Queue for received data
        self.send_running = False
        self.receive_running = False

    def ztmGetMsg(self):
        # Attempt to read a message from the ZTM controller
        
        attempts = 0
        #response = b''  # Initialize an empty byte string to store the response
        while(attempts < globals.MAX_ATTEMPTS):
            try:
                response = self.serial_port.read(globals.MSG_BYTES)
                return response
            except serial.SerialException as e:
                #print(f"Read operation failed: {e}")    
                attempts += 1        
        if attempts == globals.MAX_ATTEMPTS:
            #print(f"Failed to receive complete message.\n")   
            return False
        
    def receive_serial(self):
        """
        Continuously reads data from the serial port and processes it.
        """
        while self.receive_running:
            try:
                if self.serial_port.in_waiting > 0:
                    raw_data = self.serial_port.read(self.serial_port.in_waiting)
                    self.receive_queue.put(raw_data)  # Push received data to queue
                    #print(f"Received data: {raw_data.hex()}")
                    return raw_data
            except serial.SerialException as e:
                print(f"Error reading serial port: {e}")
                self.receive_running = False

    def send_serial(self):
        """
        Continuously sends data from the send queue to the serial port.
        """
        while self.send_running:
            try:
                data = self.send_queue.get(timeout=0.01)  # Wait for data with a timeout
                if data:
                    self.serial_port.write(data)
                    #print(f"Sent data: {data.hex()}")
            except queue.Empty:
                continue  # No data to send, loop back
            #except serial.SerialException as e:
                #print(f"Failed to write to serial port: {e}")

    def start(self):
        try:
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.01,  # Set a timeout for read operations
                write_timeout=0.01,  # Set a timeout for write operations
                xonxoff=False,
                rtscts=True,
            )
            # Increase the read and write buffer sizes
            self.serial_port.set_buffer_size(rx_size=65536, tx_size=65536)
            
            self.send_running = True
            self.receive_running = True
            self.send_thread = threading.Thread(target=self.send_serial)
            self.receive_thread = threading.Thread(target=self.receive_serial)
            self.send_thread.start()
            self.receive_thread.start()
            #print("Send and receive threads started.")
            return True
        except serial.SerialException as e:
            #print(f"Error opening serial port: {e}")
            self.serial_port = None
            return False

    def stop(self):
        self.send_running = False
        self.receive_running = False
        if self.serial_port:
            self.send_thread.join()
            self.receive_thread.join()
            self.serial_port.close()
            #print("Serial communication stopped.")

    def queue_data_for_sending(self, data):
        """
        Adds data to the send queue to be sent by the send thread.
        """
        self.send_queue.put(data)

    def get_received_data(self):
        """
        Retrieves the next available data from the receive queue.
        """
        try:
            return self.receive_queue.get_nowait()
        except queue.Empty:
            return None
            
'''
# OLD VERSION
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
    
    def ztmGetMsg(self, port):
        # Attempt to read a message from the ZTM controller
        
        attempts = 0
        #response = b''  # Initialize an empty byte string to store the response
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
    

    
    # function to read msg of 11 bytes
    def read_bytes(self):
        count = 0
        response = None

        while count < globals.MAX_ATTEMPTS:
            if self.serial_port and self.serial_port.is_open:
                try:
                    # Attempt to read 11 bytes with a timeout
                    response = self.serial_port.read(globals.MSG_BYTES)
                    if response and len(response) == globals.MSG_BYTES:
                        if response[0] not in [globals.MSG_A, globals.MSG_B, globals.MSG_C, globals.MSG_D, globals.MSG_E]:
                            print("Message received out of order.\n")
                            return None
                        else:
                            print(f"\nMCU Response (raw bytes):", response.hex())
                            return response
                    else:
                        print("No response received from MCU, retrying...")
                        count += 1
                        time.sleep(globals.ONE_SECOND)
                        return None
                except serial.SerialTimeoutException:
                    print("Read timed out, retrying...")
                    count += 1
                    time.sleep(globals.ONE_SECOND)
                    return None
            else:
                print("Serial port is not open.")
                return None
        if not response:
            print("Failed to receive response from MCU after multiple attempts.")
            return None
    
                
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
                    timeout=0.01,  # Set a timeout for read operations
                    write_timeout=0.01,  # Set a timeout for write operations
                    xonxoff=False,
                    rtscts=True,
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
'''