import tkinter as tk
from tkinter import scrolledtext
import serial
import threading

class SerialReader:
    def __init__(self, port, baudrate, callback):
        self.serial_port = serial.Serial(port, baudrate)
        self.callback = callback
        self.running = True
        self.thread = threading.Thread(target=self.read_serial)
        self.thread.start()

    def read_serial(self):
        while self.running:
            if self.serial_port.in_waiting > 0:
                data = self.serial_port.readline().decode('utf-8').strip()
                self.callback(data)

    def stop(self):
        self.running = False
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

        self.serial_reader = SerialReader(port='COM4', baudrate=9600, callback=self.update_text)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_text(self, data):
        self.text_area.insert(tk.END, data + '\n')
        self.text_area.see(tk.END)

    def on_closing(self):
        self.serial_reader.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
