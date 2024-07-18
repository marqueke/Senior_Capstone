import serial
import threading

class SerialCtrl:
    def __init__(self, port, baudrate, callback):
        self.port = port
        self.baudrate = 9600
        self.callback = callback
        self.serial_port = None
        self.thread = None
        self.running = False
        self.buffer = bytearray()

    def read_serial(self):
        while self.running and self.serial_port:
            try:
                if self.serial_port.in_waiting > 0:
                    raw_data = self.serial_port.read(self.serial_port.in_waiting)
                    #print(f"Raw data received (length {len(raw_data)}): {raw_data.hex}")
                    self.buffer.extend(raw_data)
                    
                    # Process complete frames (10 bytes each)
                    while len(self.buffer) >= 10:
                        frame = self.buffer[:10]
                        self.buffer = self.buffer[10:]
                        #print(f"Processing frame: {frame.hex}")
                        self.callback(frame)
            except serial.SerialException as e:
                print(f"Error reading serial port: {e}")
                self.running = False
    
    '''    
    to send a byte string:
    
    data_bytes = [0x0E, 0x01, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    data_to_send = bytes(data_bytes)
    serial_port.write_serial(data_to_send)

    to send an array of bytes: (i believe this is what we want)
    
    data_bytes = [0x0E, 0x01, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    serial_port.write_serial(data_bytes)
    '''
    def write_serial(self, data):
        if self.serial_port:
            try:
                self.serial_port.write(data)
                print(f"Sent data: {data}")
            except serial.SerialException as e:
                print(f"Failed to write to serial port: {e}")
        else:
            print("Serial port is not open.")

    def start(self):
        if not self.running:
            try:
                self.serial_port = serial.Serial(port=self.port, baudrate=self.baudrate, bytesize=8, 
                                                 stopbits=serial.STOPBITS_ONE, write_timeout=1.0, xonxoff=True,
                                                 parity=serial.PARITY_NONE, timeout=10)
                self.running = True
                self.thread = threading.Thread(target=self.read_serial)
                self.thread.start()
                print("Reading thread started.")
            except serial.SerialException as e:
                print(f"Error opening serial port: {e}")
                self.serial_port = None

    def stop(self):
        self.running = False
        if self.serial_port:
            self.thread.join()
            self.serial_port.close()