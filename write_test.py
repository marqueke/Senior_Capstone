import serial
import time

class SerialWriter:
    def __init__(self, port, baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None

    def open_serial(self):
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f"Serial port {self.port} opened successfully.")
            print(f"{self.serial}")
        except serial.SerialException as e:
            print(f"Failed to open serial port {self.port}: {e}")

    def write_serial(self, data):
        if self.serial:
            try:
                self.serial.write(data)
                print(f"Sent data: {data}")
                time.sleep(1)  # Give some time for the device to respond
                self.read_serial()
            except serial.SerialException as e:
                print(f"Failed to write to serial port: {e}")
        else:
            print("Serial port is not open. Call open_serial() first.")

    def read_serial(self):
        if self.serial:
            try:
                if self.serial.in_waiting > 0:
                    data = self.serial.read(self.serial.in_waiting)
                    print(f"Received data: {data.hex()}")
                else:
                    print("No data available to read.")
            except serial.SerialException as e:
                print(f"Failed to read from serial port: {e}")
        else:
            print("Serial port is not open. Call open_serial() first.")

    def send_hex_data(self, hex_string):
        # Convert hex string to bytes
        byte_data = bytes.fromhex(hex_string)
        # Send data over UART
        self.write_serial(byte_data)

    def close_serial(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
            print(f"Serial port {self.port} closed.")
        else:
            print("Serial port is not open.")

# Example usage:
if __name__ == "__main__":
    serial_writer = SerialWriter(port="COM9", baudrate=9600)
    serial_writer.open_serial()

    data_bytes = bytes([0x0E, 0x01, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    serial_writer.write_serial(data_bytes)

    data_bytes2 = bytes([0x0E, 0x01, 0x06, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    serial_writer.write_serial(data_bytes2)
    
    serial_writer.close_serial()
    
    
'''
attempt = 0

vbias_save = self.get_float_value(self.label6, 1.0, "Voltage Bias")
print(f"Saved sample bias value (float): {vbias_save}")

while attempt < 10:
#### Send user input parameters to the MCU - testing with vbias
self.parent.ztm_serial.sendMsgA(port, ztmCMD.CMD_SET_VBIAS.value, ztmSTATUS.STATUS_DONE.value, 0.5, vbias_save, 1.0)

### Read DONE from the MCU
vbias_done_response = self.parent.serial_ctrl.read_bytes()

#vbias_done_flag = 1        # debug

### Unpack data and display on the GUI
if vbias_done_response:
    if vbias_done_response[2] != ztmSTATUS.STATUS_DONE.value:
        print(f"ERROR: wrong status recieved, status value: {vbias_done_response}")
        
        self.vbias_done_flag = 0
        attempt += 1
    else:
        self.parent.ztm_serial.unpackRxMsg(vbias_done_response)
        self.vbias_done_flag = 1
        
        break
else:
    print("Failed to receive response from MCU.")
    
    self.vbias_done_flag = 0
    attempt += 1
time.sleep(1)
'''
