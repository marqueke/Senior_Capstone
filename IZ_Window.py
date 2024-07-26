# iz_window.py

from tkinter import *
from tkinter import messagebox, filedialog
from PIL import Image
import tkinter as tk
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import os, struct, time
import os, struct, time

from Sweep_IZ import SweepIZ_Window  # import the IZ Sweep Window Class
from SPI_Data_Ctrl import SerialCtrl
from Data_Com_Ctrl import DataCtrl
from value_conversion import Convert
from ztmSerialCommLibrary import ztmCMD, ztmSTATUS, usbMsgFunctions, MSG_A, MSG_B, MSG_C, MSG_D, MSG_E, MSG_F

curr_data = 0
vp_V = 0

curr_data = 0
vp_V = 0

class IZWindow:
    def __init__(self, root, port):
        self.root = root
        self.port = port

        # check if a serial connection has been established when opening the window
        if self.port == None:
            InfoMsg = f"No serial connection detected.\nConnect to USB via homepage and try again."
            messagebox.showerror("INVALID", InfoMsg) 
            self.root.destroy()

        self.port = port

        # check if a serial connection has been established when opening the window
        if self.port == None:
            InfoMsg = f"No serial connection detected.\nConnect to USB via homepage and try again."
            messagebox.showerror("INVALID", InfoMsg) 
            self.root.destroy()

        self.root.title("Acquire I-Z")
        self.root.config(bg="#d0cee2")
        self.root.geometry("750x675")   # (length x width)

        # initialize data and serial control
        self.data_ctrl = DataCtrl(9600, self.handle_data)
        self.serial_ctrl = SerialCtrl(self.port, 9600, self.data_ctrl.decode_data)
        print(f"Connected to {self.port}...")
        
        #self.data_ctrl.set_serial_ctrl(self.serial_ctrl)
        self.ztm_serial = usbMsgFunctions(self)
        self.serial_ctrl = SerialCtrl(self.port, 9600, self.data_ctrl.decode_data)
        print(f"Connected to {self.port}...")
        
        #self.data_ctrl.set_serial_ctrl(self.serial_ctrl)
        self.ztm_serial = usbMsgFunctions(self)
        
        # Initialize the widgets
        self.init_meas_widgets()
        self.init_graph_widgets()
        self.init_parameters()
        self.init_parameters()
    
    def start_reading(self):
        print("Starting to read data...")
        if self.serial_ctrl:
            print("Serial controller is initialized, starting now...")
            #self.serial_ctrl.start()
            checked = self.check_sweep_params()
            if checked:
                self.run_piezo_sweep_process()
            else:
                print("Sweep Parameters invalid. Process not started.")
            #self.send_parameters()
            #self.serial_ctrl.start()
            checked = self.check_sweep_params()
            if checked:
                self.run_piezo_sweep_process()
            else:
                print("Sweep Parameters invalid. Process not started.")
            #self.send_parameters()
        else:
            print("Serial controller is not initialized.")
    
    def stop_reading(self):
        print("Stopped reading data...")
        self.serial_ctrl.stop()
    
    def handle_data(self, raw_data):
        print(f"Handling raw data: {raw_data.hex()}")
        decoded_data = self.data_ctrl.decode_data(raw_data)
        if decoded_data:
            print("Data is being decoded...")
        else:
            print("Data decoding failed or data is incomplete")
    
    '''
    Function to error check user inputs
    '''
    def get_float_value(self, label, default_value, value_name):
        try:
            value = float(label.get())
        except ValueError:
            print(f"Invalid input for {value_name}. Using default value of {default_value}.")
            value = default_value
        return value  

    # dont think we're using, to delete if so
    def send_parameters(self):

        vpzo_min = self.get(self.label4, 0.0, "Voltage Piezo Minimum")
        vpzo_max = self.get(self.label5, 0.0, "Voltage Piezo Maximum")

        # convert vpzo to int
        vpzo_min_int = Convert.get_Vpiezo_int(vpzo_min)
        vpzo_max_int = Convert.get_Vpiezo_int(vpzo_max)
        
        print(f"Vpzo min int: {vpzo_min}, Vpzo max int: {vpzo_max}")
        
        # convert values to bytes
        vpzo_min_bytes = struct.pack('>H', vpzo_min)
        vpzo_max_bytes = struct.pack('>H', vpzo_max)
        
        
        # Construct the payload with vpzo in the correct position
        payload_min = vpzo_min_bytes
        payload_max = vpzo_max_bytes
        
        print(f"Payload Vpzo Minimum: {payload_min.hex()}")
        print(f"Payload Vpzo Maximum: {payload_max.hex()}")
        
        '''
        # SAVING BC UNSURE ABOUT VPZO
        self.parent.data_ctrl.send_command(MSG_A, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_DONE.value, payload)
        
        response = self.parent.serial_ctrl.read_serial_blocking()
        if response:
            print(f"MCU Response: {response.hex()}")
        else:
            print("No response received from MCU")
        '''

        '''
        ##### WRITE TO DISPLAY DATA AFTER RECEIVING A RESPONSE #####
        vp_V = round(ztmConvert.get_Vpiezo_float_V(struct.unpack('H',bytes(testMsg[9:11]))[0]), 3) #unpack bytes & convert
        vpStr = str(vp_V)   # format as a string
        print("\tVpiezo: " + vpStr + " V\n")
        '''

    def init_meas_widgets(self):
        # piezo extension
        self.frame1 = LabelFrame(self.root, text="ΔZ/Piezo Extension (nm)", padx=10, pady=2, bg="gray")
        self.label1 = Label(self.frame1, bg="white", width=25)
        
        # piezo voltage
        self.frame2 = LabelFrame(self.root, text="Piezo Voltage (V)", padx=10, pady=2, bg="gray")
        self.label2 = Label(self.frame2, bg="white", width=25)

        # current
        self.frame3 = LabelFrame(self.root, text="Current (nA)", padx=10, pady=2, bg="gray")
        self.label3 = Label(self.frame3, bg="white", width=25)
        
        # min voltage
        self.frame4 = LabelFrame(self.root, text="Minimum Piezo Voltage (V)", padx=10, pady=2, bg="#A7C7E7")
        self.frame4 = LabelFrame(self.root, text="Minimum Piezo Voltage (V)", padx=10, pady=2, bg="#A7C7E7")
        self.label4 = Entry(self.frame4, bg="white", width=30)
        self.label4.bind("<Return>", self.saveMinVoltage)
        self.label4.bind("<Return>", self.saveMinVoltage)
        
        # max voltage
        self.frame5 = LabelFrame(self.root, text="Maximum Piezo Voltage (V)", padx=10, pady=2, bg="#A7C7E7")
        self.frame5 = LabelFrame(self.root, text="Maximum Piezo Voltage (V)", padx=10, pady=2, bg="#A7C7E7")
        self.label5 = Entry(self.frame5, bg="white", width=30)
        self.label5.bind("<Return>", self.saveMaxVoltage)
        self.label5.bind("<Return>", self.saveMaxVoltage)
    
        # number of setpoints
        self.frame7 = LabelFrame(self.root, text="Number of Setpoints", padx=10, pady=2, bg="#A7C7E7")
        self.frame7 = LabelFrame(self.root, text="Number of Setpoints", padx=10, pady=2, bg="#A7C7E7")
        self.label9 = Entry(self.frame7, bg="white", width=30)
        self.label9.bind("<Return>", self.saveNumSetpoints)
        self.label9.bind("<Return>", self.saveNumSetpoints)

        # user notes text box
        self.frame6 = LabelFrame(self.root, text="NOTES", padx=10, pady=5, bg="#A7C7E7")
        self.label6 = Text(self.frame6, height=7, width=30)
        self.label7 = Text(self.frame6, height=1, width=8)
        self.label8 = Label(self.frame6, text="Date:", height=1, width=5)
        
        # setup the drop option menu
        self.DropDownMenu()
        
        # optional graphic parameters
        self.padx = 10
        self.pady = 10
        
        # init buttons
        self.add_btn_image1 = ctk.CTkImage(Image.open("Images/Start_Btn.png"), size=(90,35))
        self.add_btn_image2 = ctk.CTkImage(Image.open("Images/Stop_Btn.png"), size=(90,35))
        self.add_btn_image3 = ctk.CTkImage(Image.open("Images/Start_LED.png"), size=(35,35))
        self.add_btn_image4 = ctk.CTkImage(Image.open("Images/Stop_LED.png"), size=(35,35))
        
        self.start_btn = ctk.CTkButton(self.root, image=self.add_btn_image1, text="", width=90, height=35, fg_color="#d0cee2", bg_color="#d0cee2", corner_radius=0, command=self.start_reading)
        self.stop_btn = ctk.CTkButton(self.root, image=self.add_btn_image2, text="", width=90, height=35, fg_color="#d0cee2", bg_color="#d0cee2", corner_radius=0, command=self.stop_reading)
        self.start_led_btn = ctk.CTkButton(self.root, image=self.add_btn_image3, text="", width=35, height=35, fg_color="#d0cee2", bg_color="#d0cee2", corner_radius=0)
        self.stop_led_btn = ctk.CTkButton(self.root, image=self.add_btn_image4, text="", width=35, height=35, fg_color="#d0cee2", bg_color="#d0cee2", corner_radius=0)

        
        # init buttons
        self.add_btn_image1 = ctk.CTkImage(Image.open("Images/Start_Btn.png"), size=(90,35))
        self.add_btn_image2 = ctk.CTkImage(Image.open("Images/Stop_Btn.png"), size=(90,35))
        self.add_btn_image3 = ctk.CTkImage(Image.open("Images/Start_LED.png"), size=(35,35))
        self.add_btn_image4 = ctk.CTkImage(Image.open("Images/Stop_LED.png"), size=(35,35))
        
        self.start_btn = ctk.CTkButton(self.root, image=self.add_btn_image1, text="", width=90, height=35, fg_color="#d0cee2", bg_color="#d0cee2", corner_radius=0, command=self.start_reading)
        self.stop_btn = ctk.CTkButton(self.root, image=self.add_btn_image2, text="", width=90, height=35, fg_color="#d0cee2", bg_color="#d0cee2", corner_radius=0, command=self.stop_reading)
        self.start_led_btn = ctk.CTkButton(self.root, image=self.add_btn_image3, text="", width=35, height=35, fg_color="#d0cee2", bg_color="#d0cee2", corner_radius=0)
        self.stop_led_btn = ctk.CTkButton(self.root, image=self.add_btn_image4, text="", width=35, height=35, fg_color="#d0cee2", bg_color="#d0cee2", corner_radius=0)

        # put on the grid all the elements
        self.publish_meas_widgets()
    
    def publish_meas_widgets(self):
        # piezo extension
        self.frame1.grid(row=12, column=0, padx=5, pady=5, sticky=SE)
        self.label1.grid(row=0, column=0, padx=5, pady=5, sticky="s")
        
        # piezo voltage
        self.frame2.grid(row=12, column=1, padx=5, pady=5, sticky=SE)
        self.label2.grid(row=0, column=0, padx=5, pady=5)   
        
        # current
        self.frame3.grid(row=13, column=0, padx=5, pady=5, sticky=NE)
        self.label3.grid(row=0, column=0, padx=5, pady=5, sticky="n") 

        # min voltage
        self.frame4.grid(row=11, column=0, padx=5, pady=5, sticky="n")
        self.label4.grid(row=0, column=0, padx=5, pady=5)
        
        # max voltage
        self.frame5.grid(row=11, column=1, padx=5, pady=5, sticky="n")
        self.label5.grid(row=0, column=0, padx=5, pady=5)

        # number of setpoints
        self.frame7.grid(row=13, column=1, padx=5, pady=5, sticky="n")
        self.label9.grid(row=0, column=0, padx=5, pady=5)
        
        # Positioning the notes section
        self.frame6.grid(row=11, column=7, rowspan=3, pady=5, sticky="n")
        self.label6.grid(row=1, column=0, pady=5, columnspan=3, rowspan=3) 
        self.label7.grid(row=0, column=2, pady=5, sticky="e")
        self.label8.grid(row=0, column=2, pady=5, sticky="w")
        
        # Positioning the file drop-down menu
        self.drop_menu.grid(row=0, column=0, padx=self.padx, pady=self.pady)

        self.start_btn.grid(row=1, column=10, padx=5, pady=15, sticky="s")
        self.stop_btn.grid(row=2, column=10, padx=5, sticky="n")
        self.stop_led_btn.grid(row=1, column=11, padx=5, pady=15, sticky="sw")
        # need to switch RG LED on process state
        #self.start_led_btn.grid(row=1, column=11, padx=5, pady=15, sticky="sw")

    def init_parameters(self):
        self.min_voltage = None
        self.max_voltage = None
        self.num_setpoints = None
        self.piezo_volt_range = None
        self.volt_per_step = None
        # need to switch RG LED on process state
        #self.start_led_btn.grid(row=1, column=11, padx=5, pady=15, sticky="sw")

    def init_parameters(self):
        self.min_voltage = None
        self.max_voltage = None
        self.num_setpoints = None
        self.piezo_volt_range = None
        self.volt_per_step = None

    def saveMinVoltage(self, event):
        if 0 <= float(self.label4.get()) <= 10:
            self.min_voltage = float(self.label4.get())
            print(f"Saved min voltage value: {self.min_voltage}")
        else:
            InfoMsg = f"Invalid range. Stay within 0 - 10 V."
            messagebox.showerror("INVALID", InfoMsg)

    def saveMaxVoltage(self, event):
        if 0 <= float(self.label5.get()) <= 10:
            self.max_voltage = float(self.label5.get())
            print(f"Saved min voltage value: {self.max_voltage}")
        else:
            InfoMsg = f"Invalid range. Stay within 0 - 10 V."
            messagebox.showerror("INVALID", InfoMsg) 

    def saveNumSetpoints(self, event):
        self.num_setpoints = int(self.label9.get())
        self.num_setpoints = int(self.label9.get())
        print(f"Saved number of setpoints value: {self.num_setpoints}")

    # current, piezo voltage, piezo extension
    def update_label(self):
        #self.label1.configure(text=f"{self.piezo_distance:.3f} nm") # piezo extension
        self.label2.configure(text=f"{vp_V:.3f} V") # piezo voltage
        self.label3.configure(text=f"{curr_data:.3f} nA") # current
        self.label2.after(100, self.update_label)

    def check_sweep_params(self):
        if self.min_voltage == None or self.min_voltage < 0 or self.min_voltage > 10:
            InfoMsg = f"Invalid Min Voltage. Please update your paremeters."
            messagebox.showerror("INVALID", InfoMsg)
            return False
        
        if self.max_voltage == None or self.max_voltage <= 0 or self.max_voltage > 10:
            InfoMsg = f"Invalid Max Voltage. Please update your paremeters."
            messagebox.showerror("INVALID", InfoMsg) 
            return False

        if self.num_setpoints == None or self.num_setpoints <= 0:
            InfoMsg = f"Invalid Number of Setpoints. Please update your paremeters."
            messagebox.showerror("INVALID", InfoMsg) 
            return False

        self.piezo_volt_range = self.max_voltage - self.min_voltage
        self.volt_per_step = self.piezo_volt_range / self.num_setpoints

        if self.piezo_volt_range <= 0:
            InfoMsg = f"Invalid sweep range. Max value must be higher than Min value."
            messagebox.showerror("INVALID", InfoMsg) 
            return False
        
        if self.volt_per_step < 0.001:
            InfoMsg = f"Invalid Step Size.\nStep size: {self.volt_per_step:.6f}\nStep size needs to be greater than or equal 0.001V\nDecrease number of points or increase voltage range"
            messagebox.showerror("INVALID", InfoMsg) 
            return False
        
        return True
            

    def run_piezo_sweep_process(self):

        # starting point for piezo sweep, set to user-input minimum voltage
        # starting point for piezo sweep, set to user-input minimum voltage
        self.vpiezo = self.min_voltage
        # start to display parameters to user
        self.label2.after(1, self.update_label)
        # start to display parameters to user
        self.label2.after(1, self.update_label)

        for i in range(0, self.num_setpoints):
            print(f"Sending MSG_A to port: {self.port}")

            # sending vpiezo to MCU, looking for a DONE status in return
            success = self.send_msg_retry(self.port, MSG_A, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_CLR.value, 0, 0, self.vpiezo)
            if not success:
                InfoMsg = f"Could not verify communication with MCU.\nSweep process aborted."
                messagebox.showerror("INVALID", InfoMsg) 
                return
            
            # sending a REQUEST_FOR_DATA command to MCU to receive current and vpiezo measurements
            dataSuccess = self.send_msg_retry(self.port, MSG_C, ztmCMD.CMD_REQ_DATA.value, ztmSTATUS.STATUS_CLR.value)
            if not dataSuccess:
                InfoMsg = f"Did not receive data from MCU.\nSweep process aborted."
                messagebox.showerror("INVALID", InfoMsg) 
                return

            # increment the piezo that sets the MCU, and increment through the number of setpoints for the for loop
            self.vpiezo += self.volt_per_step
        for i in range(0, self.num_setpoints):
            print(f"Sending MSG_A to port: {self.port}")

            # sending vpiezo to MCU, looking for a DONE status in return
            success = self.send_msg_retry(self.port, MSG_A, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_CLR.value, 0, 0, self.vpiezo)
            if not success:
                InfoMsg = f"Could not verify communication with MCU.\nSweep process aborted."
                messagebox.showerror("INVALID", InfoMsg) 
                return
            
            # sending a REQUEST_FOR_DATA command to MCU to receive current and vpiezo measurements
            dataSuccess = self.send_msg_retry(self.port, MSG_C, ztmCMD.CMD_REQ_DATA.value, ztmSTATUS.STATUS_CLR.value)
            if not dataSuccess:
                InfoMsg = f"Did not receive data from MCU.\nSweep process aborted."
                messagebox.showerror("INVALID", InfoMsg) 
                return

            # increment the piezo that sets the MCU, and increment through the number of setpoints for the for loop
            self.vpiezo += self.volt_per_step
            self.num_setpoints += 1
        


    '''
    Function to send a message to the MCU and retry if we do
    not receive expected response
    '''
    def send_msg_retry(self, port, msg_type, cmd, status, *params, max_attempts=2, sleep_time=0.5):
        
        attempt = 0
        
        while attempt < max_attempts:
            if msg_type == MSG_A:
                self.ztm_serial.sendMsgA(port, cmd, status, *params)
            elif msg_type == MSG_B:
                self.ztm_serial.sendMsgB(port, cmd, status, *params)
            elif msg_type == MSG_C:
                self.ztm_serial.sendMsgC(port, cmd, status, *params)
            elif msg_type == MSG_D:
                self.ztm_serial.sendMsgD(port, cmd, status, *params)
            elif msg_type == MSG_E:
                self.ztm_serial.sendMsgE(port, cmd, status, *params)
            else:
                raise ValueError(f"Unsupported message type: {msg_type}")
            
            self.response = self.serial_ctrl.ztmGetMsg()
            
            print(f"Serial response: {self.response}")
            
            ### Unpack data and display on the GUI
            if self.response:
                if self.response[2] == ztmSTATUS.STATUS_DONE.value:
                    self.ztm_serial.unpackRxMsg(self.response)
                    print(f"SUCCESS. Response received: {self.response}")
                    
                    return True
                elif self.response[2] == ztmSTATUS.STATUS_MEASUREMENTS.value:
                    curr_data = round(struct.unpack('f', bytes(self.response[3:7]))[0], 3) #unpack bytes & convert
                    cStr = str(curr_data)  # format as a string
                    print("Received values\n\tCurrent: " + cStr + " nA\n")
                        
                    vb_V = round(Convert.get_Vbias_float(struct.unpack('H',bytes(self.response[7:9]))[0]), 3) #unpack bytes & convert
                    vbStr = str(vb_V)   # format as a string
                    print("\tVbias: " + vbStr + " V\n")
                        # vpiezo
                    vp_V = round(Convert.get_Vpiezo_float(struct.unpack('H',bytes(self.response[9:11]))[0]), 3) #unpack bytes & convert
                    vpStr = str(vp_V)   # format as a string
                    print("\tVpiezo: " + vpStr + " V\n")
                    
                    #update for windows, params
                    #self.label3.configure(text=f"{curr_data:.3f}")
                    

                    return True
                elif self.response[2] == ztmSTATUS.STATUS_ACK.value:
                    print("Received ACK from MCU.")
                    
                    return True
                else:
                    print(f"ERROR. Wrong status recieved: {self.response}")

                    # if we want to decode the command or status & print to the console....
                    cmdRx = ztmCMD(self.response[1])
                    print("Received : " + cmdRx.name)
                    statRx = ztmSTATUS(self.response[2])
                    print("Received : " + statRx.name + "\n")
                    
                    attempt += 1
            else:
                print("ERROR. Failed to receive response from MCU.")

                attempt += 1
            time.sleep(sleep_time)
        return False


    '''
    Function to send a message to the MCU and retry if we do
    not receive expected response
    '''
    def send_msg_retry(self, port, msg_type, cmd, status, *params, max_attempts=2, sleep_time=0.5):
        
        attempt = 0
        
        while attempt < max_attempts:
            if msg_type == MSG_A:
                self.ztm_serial.sendMsgA(port, cmd, status, *params)
            elif msg_type == MSG_B:
                self.ztm_serial.sendMsgB(port, cmd, status, *params)
            elif msg_type == MSG_C:
                self.ztm_serial.sendMsgC(port, cmd, status, *params)
            elif msg_type == MSG_D:
                self.ztm_serial.sendMsgD(port, cmd, status, *params)
            elif msg_type == MSG_E:
                self.ztm_serial.sendMsgE(port, cmd, status, *params)
            else:
                raise ValueError(f"Unsupported message type: {msg_type}")
            
            self.response = self.serial_ctrl.ztmGetMsg()
            
            print(f"Serial response: {self.response}")
            
            ### Unpack data and display on the GUI
            if self.response:
                if self.response[2] == ztmSTATUS.STATUS_DONE.value:
                    self.ztm_serial.unpackRxMsg(self.response)
                    print(f"SUCCESS. Response received: {self.response}")
                    
                    return True
                elif self.response[2] == ztmSTATUS.STATUS_MEASUREMENTS.value:
                    curr_data = round(struct.unpack('f', bytes(self.response[3:7]))[0], 3) #unpack bytes & convert
                    cStr = str(curr_data)  # format as a string
                    print("Received values\n\tCurrent: " + cStr + " nA\n")
                        
                    vb_V = round(Convert.get_Vbias_float(struct.unpack('H',bytes(self.response[7:9]))[0]), 3) #unpack bytes & convert
                    vbStr = str(vb_V)   # format as a string
                    print("\tVbias: " + vbStr + " V\n")
                        # vpiezo
                    vp_V = round(Convert.get_Vpiezo_float(struct.unpack('H',bytes(self.response[9:11]))[0]), 3) #unpack bytes & convert
                    vpStr = str(vp_V)   # format as a string
                    print("\tVpiezo: " + vpStr + " V\n")
                    
                    #update for windows, params
                    #self.label3.configure(text=f"{curr_data:.3f}")
                    

                    return True
                elif self.response[2] == ztmSTATUS.STATUS_ACK.value:
                    print("Received ACK from MCU.")
                    
                    return True
                else:
                    print(f"ERROR. Wrong status recieved: {self.response}")

                    # if we want to decode the command or status & print to the console....
                    cmdRx = ztmCMD(self.response[1])
                    print("Received : " + cmdRx.name)
                    statRx = ztmSTATUS(self.response[2])
                    print("Received : " + statRx.name + "\n")
                    
                    attempt += 1
            else:
                print("ERROR. Failed to receive response from MCU.")

                attempt += 1
            time.sleep(sleep_time)
        return False
        
    # file drop-down menu
    def DropDownMenu(self):
        self.menubar = tk.Menu(self.root)
        
        #self.custom_font = tkFont.Font(size=8)
        
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Save", command=self.save_graph)
        self.filemenu.add_command(label="Save As", command=self.save_graph_as)
        self.filemenu.add_command(label="Export (.txt)", command=self.export_data)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.root.quit)
        
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        
        self.root.config(menu=self.menubar)

    def menu_selection(self, selection):
        if selection == "Exit":
            self.root.destroy()
        elif selection == "Save":
            self.save_graph()
        elif selection == "Save As":
            self.save_graph_as()
        elif selection == "Export (.txt)":
            self.export_data()
    
    def save_graph(self):
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        default_filename = os.path.join(downloads_folder, "iz_graph.png")
        self.fig.savefig(default_filename)
        messagebox.showinfo("Save Graph", f"Graph saved in Downloads as {default_filename}")
        
    def save_graph_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if file_path:
            self.fig.savefig(file_path)
            messagebox.showinfo("Save Graph As", f"Graph saved as {file_path}")
    
    def export_data(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write("Sample data to export")
            messagebox.showinfo("Export Data", f"Data exported as {file_path}")
                
    def init_graph_widgets(self):
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('Delta Z (nm)')
        self.ax.set_ylabel('Tunneling Current (A)')
        self.fig.set_figwidth(7)
        self.fig.set_figheight(4.5)
        
        # Create a canvas to embed the figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=1, column=0, columnspan=10, rowspan=8, padx=10, pady=10)

        # Start animation
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval=1000, cache_frame_data=False)
        
    def animate(self, i):
        try:
            graph_data = open('fakedata.txt', 'r').read()
            lines = graph_data.split('\n')
            xdata = []
            ydata = []
            for line in lines:
                if len(line) > 1:
                    x, y = line.split(',')
                    xdata.append(float(x))
                    ydata.append(float(y))
            self.ax.clear()
            self.ax.plot(xdata, ydata, c='#64B9FF')
            
            self.ax.set_title('Tunneling Current')
            self.ax.set_xlabel('Piezo Voltage (V)')
            self.ax.set_ylabel('Current (A)')
        except FileNotFoundError:
            pass