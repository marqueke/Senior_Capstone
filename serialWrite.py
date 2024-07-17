import serial

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
        except serial.SerialException as e:
            print(f"Failed to open serial port {self.port}: {e}")

    def write_bytes(self, data):
        if self.serial:
            try:
                self.serial.write(data)
                print(f"Sent data: {data}")
            except serial.SerialException as e:
                print(f"Failed to write to serial port: {e}")
        else:
            print("Serial port is not open. Call open_serial() first.")

    def send_hex_data(self, hex_string):
        # Convert hex string to bytes
        byte_data = bytes.fromhex(hex_string)
        # Send data over UART
        self.serial.write(byte_data)

    def close_serial(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
            print(f"Serial port {self.port} closed.")
        else:
            print("Serial port is not open.")

# Example usage:
if __name__ == "__main__":
    serial_writer = SerialWriter(port="COM6", baudrate=9600)
    serial_writer.open_serial()
    # data_to_send = b'test my test your test'

    # data_bytes = [0x52, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41] # test
    data_bytes = [0x0E, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41]
    data_to_send = bytes(data_bytes)
    serial_writer.write_bytes(data_to_send)
    serial_writer.close_serial()

    # data_to_send = bytes.fromhex(data_bytes)  

    # data_bytes = [0x0E, 0x42, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1, 0x4]
    # # data_to_send = b'test my test your test'
    # data_to_send = bytes(data_bytes)
    # serial_writer.write_bytes(data_to_send)
    # # serial_writer.send_hex_data(data_bytes)

    serial_writer.close_serial()
