import tkinter as tk
from tkinter import scrolledtext
import serial
import threading
from PIL import Image, ImageTk
import PIL
import customtkinter as ctk

class SerialReader:
    def __init__(self, port, baudrate, callback):
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self.serial_port = None
        self.thread = None
        self.running = False

    def read_serial(self):
        while self.running and self.serial_port:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='replace').strip()
                    print(f"Received data: {data}")  # Debugging print statement
                    self.callback(data)
            except serial.SerialException as e:
                print(f"Error reading serial port: {e}")
                self.running = False

    def write_serial(self, bytes):
        while self.running and self.serial_port:
            try:
                ser = serial.Serial("COM6", serial.EIGHTBITS)
                ser.write(bytes)
                # print(f"Sending data: {bytes}")
                ser.close()
                    
            except serial.SerialException as e:
                print(f"Error writing to serial port: {e}")
                self.running = False

    def start(self):
        if not self.running:
            try:
                self.serial_port = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=1)
                self.running = True
                self.thread = threading.Thread(target=self.read_serial)
                self.thread.start()
            except serial.SerialException as e:
                print(f"Error opening serial port: {e}")
                self.serial_port = None

    def stop(self):
        self.running = False
        if self.serial_port:
            self.thread.join()
            self.serial_port.close()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("STM32 Serial Data Display")

        self.label = tk.Label(root, text="Received Data:")
        self.label.pack(pady=10)

        self.frame = tk.Frame(root, relief=tk.RAISED, borderwidth=2)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.text_area = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, height=20, width=60)
        self.text_area.pack(fill=tk.BOTH, expand=True)

        
        self.serial_reader = SerialReader(port='COM6', baudrate=9600, callback=self.update_text)

        self.serial_reader.write_serial()
        data_bytes = [0xEE, 0xFF, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        data_to_send = bytes(data_bytes)
        self.serial_reader.write_serial(data_to_send)
        self.serial_reader = SerialReader(port='COM9', baudrate=9600, callback=self.update_text)

        self.add_btn_image4 = ctk.CTkImage(Image.open("Images/Start_Btn.png"), size=(90,35))
        self.start_btn = ctk.CTkButton(master=root, image=self.add_btn_image4, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.start_reading)
        self.start_btn.pack(pady=10)  # Using pack to add the button

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_text(self, data):
        self.text_area.insert(tk.END, data + '\n')
        self.text_area.see(tk.END)

    def start_reading(self):
        self.serial_reader.start()

    def on_closing(self):
        self.serial_reader.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    # app = App(root)

    
    root.mainloop()
