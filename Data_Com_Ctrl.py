import serial
import threading
import queue
import serial.tools.list_ports
from tkinter import messagebox

class SerialController:
    def __init__(self, port, baudrate, callback):
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self.serial_connection = None
        self.running = False
        self.thread = None
        self.queue = queue.Queue()

    def start(self, root):
        try:
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self.read_data)
            self.thread.start()
            self.process_queue(root)
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            messagebox.showerror("Serial Error", f"Error opening serial port: {e}")

    def read_data(self):
        while self.running:
            try:
                data = self.serial_connection.readline().decode(errors='replace').strip()
                if data:
                    self.queue.put(data)
            except serial.SerialException as e:
                print(f"Serial read error: {e}")
                self.stop()

    def process_queue(self, root):
        while not self.queue.empty():
            data = self.queue.get()
            self.callback(data)
        if self.running:
            root.after(100, self.process_queue, root)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.serial_connection:
            self.serial_connection.close()

    def SerialOpen(self, com_gui):
        try:
            self.serial_connection = serial.Serial(self.port, self.baudrate)
            self.running = True
            self.thread = threading.Thread(target=self.read_data)
            self.thread.start()
            return True
        except Exception as e:
            print(f"Failed to open serial port: {e}")
            return False

    def SerialClose(self, com_gui):
        self.stop()

    def getCOMList(self):
        self.com_list = [port.device for port in serial.tools.list_ports.comports()]
        if not self.com_list:
            self.com_list = ['No COM ports found']