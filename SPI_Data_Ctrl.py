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

    def read_serial(self):
        while self.running and self.serial_port:
            try:
                if self.serial_port.in_waiting > 0:
                    raw_data = self.serial_port.read(10)    # Read 10 byte data frame
                    data = raw_data.decode('utf-8', errors='replace').strip()
                    #data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='replace').strip()
                    print(f"Raw data: {raw_data}")  # Debugging print statement
                    print(f"Processed data: {data}")
                    self.callback(data)
            except serial.SerialException as e:
                print(f"Error reading serial port: {e}")
                self.running = False

    def start(self):
        if not self.running:
            try:
                self.serial_port = serial.Serial(port=self.port, baudrate=self.baudrate, bytesize=8, 
                                                 stopbits=serial.STOPBITS_ONE, write_timeout=1.0, xonxoff=True,
                                                 parity=serial.PARITY_NONE, timeout=10)
                self.running = True
                self.thread = threading.Thread(target=self.read_serial)
                self.thread.start()
            except serial.SerialException as e:
                print(f"Error reading serial port: {e}")
                self.serial_port = None

    def stop(self):
        self.running = False
        if self.serial_port:
            self.thread.join()
            self.serial_port.close()