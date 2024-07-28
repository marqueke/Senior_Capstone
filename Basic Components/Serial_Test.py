import tkinter as tk
from tkinter import scrolledtext
import serial
import threading
import time
from PIL import Image, ImageTk
import customtkinter as ctk
from ztmSerialCommLibrary import usbMsgFunctions, ztmCMD, ztmSTATUS, MSG_A, MSG_B, MSG_C, MSG_D, MSG_E
import struct 

# Constants for MSG C
MSG_C = 0x0C
#ztmCMD = type('ztmCMD', (), {'CMD_CLR': type('value', (), {'value': 0x01})})()
#ztmSTATUS = type('ztmSTATUS', (), {'STATUS_RDY': type('value', (), {'value': 0x02}),
#                                   'STATUS_ACK': type('value', (), {'value': 0x06})})()

class SerialReader:
    def __init__(self, port, baudrate, callback):
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self.serial_port = None
        self.thread = None
        self.running = False

        self.ztm_serial = usbMsgFunctions(self)
        
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

    def send_msg_retry(self, port, msg_type, cmd, status, status_response, *params, max_attempts=10, sleep_time=0.5):
        padByte = [0x00]
        attempt = 0
        msg_print = [msg_type, cmd, status]
        
        # Convert each element in msg_print to a hex string
        msg_print_hex = ' '.join(format(x, '02X') for x in msg_print)
        print(f"\nMESSAGE BEING SENT: {msg_print_hex}")
        
        while attempt < max_attempts:
            print(f"\n========== ATTEMPT NUMBER: {attempt + 1} ==========")
            payload = padByte * 8
            messageC = struct.pack('BBBBBBBBBBB', msg_type, cmd, status, *payload)
            try:
                for byte in messageC:
                    port.write(serial.to_bytes([byte]))
                port.flush()  
            except serial.SerialException as e:
                print(f"Write operation failed: {e}")
                attempt += 1
                time.sleep(sleep_time)
                continue
            
            testMsg = self.ztmGetMsg(port)
            
            if testMsg:
                testMsg_hex = [b for b in testMsg]
                print(f"Serial response: {testMsg_hex}")
                
                if testMsg_hex[2] == status_response and len(testMsg) == 11:
                    unpackResponse = self.ztm_serial.unpackRxMsg(testMsg)
                    print(f"Received correct status response from MCU: {testMsg[2]}")
                    return True
                else:
                    print(f"ERROR. Wrong response received: {testMsg}")
                    print(f"Length of message received: {len(testMsg)}")
                    print(f"\tReceived status: {testMsg[2]}")
                    print(f"\tExpected status: {status_response}")
            else:
                print("ERROR. Failed to receive response from MCU.")
            
            time.sleep(sleep_time)
            attempt += 1

        print(f"Failed to send message after {max_attempts} attempts.")
        return False

    def ztmGetMsg(self, port):
        attempts = 0
        while attempts < 10:
            try:
                response = port.read(11)
                return response
            except serial.SerialException as e:
                print(f"Read operation failed: {e}")
                attempts += 1        
        if attempts == 10:
            print(f"Failed to receive complete message.\n")   
            return False

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

        self.serial_reader = SerialReader(port='COM11', baudrate=460800, callback=self.update_text)

        self.add_btn_image4 = ctk.CTkImage(Image.open("Images/Start_Btn.png"), size=(90,35))
        self.start_btn = ctk.CTkButton(master=root, image=self.add_btn_image4, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.start_reading)
        self.start_btn.pack(pady=10)  # Using pack to add the button

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_text(self, data):
        self.text_area.insert(tk.END, data + '\n')
        self.text_area.see(tk.END)

    def start_reading(self):
        self.serial_reader.start()
        port = self.serial_reader.serial_port
        if port:
            self.serial_reader.send_msg_retry(port, MSG_C, ztmCMD.CMD_CLR.value, ztmSTATUS.STATUS_RDY.value, ztmSTATUS.STATUS_ACK.value)

    def on_closing(self):
        self.serial_reader.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
