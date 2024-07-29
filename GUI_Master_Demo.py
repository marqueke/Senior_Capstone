from tkinter import *
from tkinter import messagebox, filedialog
from PIL import Image, ImageGrab
import customtkinter as ctk
import serial, re, os, struct, time
import serial.tools.list_ports
import tkinter as tk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from IV_Window import IVWindow  # import the IV Window Class
from IZ_Window import IZWindow  # import the IV Window Class
from Data_Com_Ctrl import DataCtrl
from value_conversion import Convert
from ztmSerialCommLibrary import usbMsgFunctions, ztmCMD, ztmSTATUS, MSG_A, MSG_B, MSG_C, MSG_D, MSG_E, MSG_F
from SPI_Data_Ctrl import SerialCtrl
import datetime
import matplotlib.dates as mdates
import csv

import random # for graph - delete later

# global variables
curr_setpoint = None
curr_data = None

vbias_save = None
vbias_done_flag = 0

sample_rate_save = None
sample_rate_done_flag = 0

sample_size_save = None
sample_size_done_flag = 0

home_pos_total_steps = None
curr_pos_total_steps = None

tip_app_total_steps = None

class RootGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Homepage")
        self.root.config(bg="#eeeeee")
        self.root.geometry("1100x650")
        self.root.resizable(False, False)
        
        # Add a method to quit the application
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
        
        # initialize data and serial control
        self.data_ctrl = DataCtrl(9600, self.handle_data)
        self.serial_ctrl = SerialCtrl(None, 9600, self.data_ctrl.decode_data)
        self.data_ctrl.set_serial_ctrl(self.serial_ctrl)
        self.ztm_serial = usbMsgFunctions(self)
        
        # Initialize other components
        self.meas_gui = MeasGUI(self.root, self)
        self.graph_gui = GraphGUI(self.root, self.meas_gui)
        self.com_gui = ComGUI(self.root, self)
        
    def quit_application(self):
        print("\nQUITTING APPLICATION")
        if self.serial_ctrl:
            self.serial_ctrl.stop()
        self.root.quit()
    
    def start_reading(self):
        print("Starting to read data...")
        if self.serial_ctrl:
            print("Serial controller is initialized, starting now...")
            #self.meas_gui.start_seeking()
            self.meas_gui.enable_periodics()
        else:
            print("Serial controller is not initialized.")
    
    def stop_reading(self):
        print("Stopped reading data...")
        self.meas_gui.send_msg_retry(self.serial_ctrl.serial_port, MSG_C, ztmCMD.CMD_PERIODIC_DATA_DISABLE, ztmSTATUS.STATUS_DONE)
        #self.serial_ctrl.stop()    # used to close the serial read thread- but we do not want that

    
    def handle_data(self, raw_data):
        print(f"Handling raw data: {raw_data.hex()}")
        decoded_data = self.data_ctrl.decode_data(raw_data)
        if decoded_data:
            print("Data is being decoded...")
            self.update_distance(*decoded_data)
        else:
            print("Data decoding failed or data is incomplete")


# Class to setup and create the communication manager with MCU
class ComGUI:
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        #self.serial_ctrl = None
        self.frame = LabelFrame(root, text="Com Manager", padx=5, pady=5, bg="white")
        self.label_com = Label(self.frame, text="Available Port(s): ", bg="white", width=15, anchor="w")
        
        # Setup the Drop option menu
        self.ComOptionMenu()

        # Add the control buttons for refreshing the COMs & Connect
        self.btn_refresh = Button(self.frame, text="Refresh", width=10, command=self.com_refresh)
        self.btn_connect = Button(self.frame, text="Connect", width=10, state="disabled", command=self.serial_connect)
        
        # Optional Graphic parameters
        self.padx = 7
        self.pady = 5

        # Put on the grid all the elements
        self.publish()

    def publish(self):
        self.frame.grid(row=1, column=0, rowspan=3, columnspan=3, padx=5, pady=5)
        self.label_com.grid(column=1, row=2)
        self.drop_com.grid(column=2, row=2, padx=self.padx)
        self.btn_refresh.grid(column=3, row=2, padx=self.padx)
        self.btn_connect.grid(column=3, row=3, padx=self.padx)

    def ComOptionMenu(self):
        ports = serial.tools.list_ports.comports()
        self.serial_ports = [port.device for port in ports]
        self.clicked_com = StringVar()
        self.clicked_com.set("-" if self.serial_ports else "No COM port found")
        self.drop_com = OptionMenu(self.frame, self.clicked_com, *self.serial_ports, command=self.connect_ctrl)
        self.drop_com.config(width=10)
    
    def connect_ctrl(self, widget):
        if self.clicked_com.get() == "-":
            self.btn_connect["state"] = "disabled"
        else:
            self.btn_connect["state"] = "active"

    def com_refresh(self):
        print("Refresh")
        self.drop_com.destroy()
        self.ComOptionMenu()
        self.drop_com.grid(column=2, row=2, padx=self.padx)
        logic = []
        self.connect_ctrl(logic)

    def serial_connect(self):
        if self.btn_connect["text"] == "Connect":
            port = self.clicked_com.get()
            try:
                # Attempt to open the serial port to check if it is already in use
                test_serial = serial.Serial(port)
                test_serial.close()

                # If the port is available, proceed with the connection
                self.parent.serial_ctrl.port = port
                #self.parent.serial_ctrl.serial_port = serial.Serial(port)  # Open the serial port
                #self.parent.meas_gui.update_port(self.parent.serial_ctrl.serial_port)  # Update the port in MeasGUI
                print(f"Connecting to {port}...")
                self.btn_connect["text"] = "Disconnect"
                self.btn_refresh["state"] = "disable"
                self.drop_com["state"] = "disable"
                InfoMsg = f"Successful UART connection using {self.clicked_com.get()}."
                messagebox.showinfo("Connected", InfoMsg)
                
                serial_response = self.parent.serial_ctrl.start()
                
                if serial_response:
                    self.startup_routine()
                else:
                    self.btn_connect["text"] = "Connect"
                    self.btn_refresh["state"] = "active"
                    self.drop_com["state"] = "active"
                    InfoMsg = f"Failed to connect to {self.clicked_com.get()}."
                    messagebox.showerror("Connection Error", InfoMsg)
                    print(f"Failed to connect to {port}.")
                    self.parent.serial_ctrl.running = False
                    
            except serial.SerialException as e:
                self.btn_connect["text"] = "Connect"
                self.btn_refresh["state"] = "active"
                self.drop_com["state"] = "active"
                InfoMsg = f"Failed to connect to {self.clicked_com.get()}: {e}"
                messagebox.showerror("Connection Error", InfoMsg)
                print(f"Failed to connect to {port}: {e}")
                self.parent.serial_ctrl.running = False
        else:
            if self.parent.serial_ctrl:
                self.parent.serial_ctrl.stop()
            self.btn_connect["text"] = "Connect"
            self.btn_refresh["state"] = "active"
            self.drop_com["state"] = "active"
            InfoMsg = f"UART connection using {self.clicked_com.get()} is now closed."
            messagebox.showwarning("Disconnected", InfoMsg)
            print("Disconnected")

    def startup_routine(self):
        print("*************** BEGINNING STARTUP ROUTINE ***************")
        port = self.parent.serial_ctrl.serial_port
        print(f"{port}")
        # check for port connection
        if port is None:
            print("Port is not connected.")
        
        msg_response = self.parent.meas_gui.send_msg_retry(port, MSG_C, ztmCMD.CMD_CLR.value, ztmSTATUS.STATUS_RDY.value, ztmSTATUS.STATUS_STEP_COUNT.value)
        
        if msg_response:
            print("SUCCESS. Startup routine completed.")
        else:
            self.btn_connect["text"] = "Connect"
            self.btn_refresh["state"] = "active"
            self.drop_com["state"] = "active"
            InfoMsg = f"Failed to connect to {self.clicked_com.get()}."
            messagebox.showerror("Connection Error", InfoMsg)
            print(f"Failed to connect to {self.clicked_com.get()}.")            
            #self.parent.serial_ctrl.running = False
            print("ERROR. Startup routine not completed.")
            self.parent.serial_ctrl.running = False
            

  
# class for measurements/text box widgets in homepage
class MeasGUI:
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        
        # initialize data attributes for continuous update
        self.distance   = 0.0
        self.adc_curr   = 0.0
        
        # vpzo adjust
        self.vpzo_down  = 0
        self.vpzo_up    = 0
        self.total_voltage = 0.0
        
        # stepper motor adjust
        self.step_up    = 0
        self.step_down  = 0
        
        self.initialize_widgets()
        
    def initialize_widgets(self):
        # optional graphic parameters
        self.padx = 20
        self.pady = 10
        
        # sample rate adjust
        self.frame8 = LabelFrame(self.root, text="", padx=5, pady=5, bg="#ADD8E6")
        self.label_sample_rate = Label(self.frame8, text="Sample Rate: ", bg="#ADD8E6", width=11, anchor="w")
        self.sample_rate_var = StringVar()
        self.sample_rate_var.set("-")
        self.sample_rate_menu = OptionMenu(self.frame8, self.sample_rate_var, "25 kHz", "12.5 kHz", "37.5 kHz", "10 kHz", "5 kHz", command=self.saveSampleRate)  
        self.sample_rate_menu.config(width=7)
        
        # sample size
        self.sample_size = Entry(self.frame8, width=13)
        self.sample_size_label = Label(self.frame8, text="Sample Size: ", bg="#ADD8E6", width=11, anchor="w")
        self.sample_size.bind("<Return>", self.sendSampleSize)
        
        self.label_sample_rate.grid(column=1, row=1)
        self.sample_rate_menu.grid(column=2, row=1) #, padx=self.padx)
        self.frame8.grid(row=13, column=4, padx=5, pady=5, sticky="")
        
        self.sample_size.grid(column=2, row=2, pady=5)
        self.sample_size_label.grid(column=1, row=2)

        # fine adjust step size
        self.frame9 = LabelFrame(self.root, text="", padx=5, pady=5, bg="#ADD8E6")
        self.label_fine_adjust = Label(self.frame9, text="Step Size: ", bg="#ADD8E6", width=8, anchor="w")
        self.fine_adjust_var = StringVar()
        self.fine_adjust_var.set("-")
        self.fine_adjust_menu = OptionMenu(self.frame9, self.fine_adjust_var, "Full", "Half", "Quarter", "Eighth", command=self.saveStepperMotorAdjust) 
        self.fine_adjust_menu.config(width=6)

        self.label_fine_adjust.grid(column=1, row=1)
        self.fine_adjust_menu.grid(column=1, row=2) #, padx=self.padx)
        self.frame9.grid(row=12, column=2, rowspan=2, columnspan=2, padx=5, pady=5, sticky="")
        self.label_fine_adjust_inc = Label(self.frame9, text="Approx. Dist", bg="#ADD8E6", width=9, anchor="w")

        self.label5 = Label(self.frame9, bg="white", width=10)
        self.label_fine_adjust_inc.grid(column=2, row=1)
        self.label5.grid(column=2, row=2, padx=5, pady=5)

        # vpiezo adjust step size
        self.frame10 = LabelFrame(self.root, text="", padx=5, pady=5, bg="#d0cee2")
        self.label_vpeizo_delta = Label(self.frame10, text="Vpiezo ΔV (V):", bg="#d0cee2", width=11, anchor="w")
        self.label_vpeizo_delta.grid(column=1, row=1)
        self.frame10.grid(row=7, column=2, rowspan=4, columnspan=2, padx=5, pady=5, sticky="")
        self.label_vpeizo_delta_distance = Label(self.frame10, text="Approx. Dist", bg="#d0cee2", width=9, anchor="w")
        self.label_vpeizo_delta_distance.grid(column=2, row=1)
        self.label10 = Entry(self.frame10, bg="white", width=10)
        self.label10.bind("<Return>", self.savePiezoValue)
        self.label11 = Label(self.frame10, bg="white", width=10)
        self.label10.grid(column=1, row=2, padx=5)
        self.label11.grid(column=2, row=2, padx=5)
        self.label_vpeizo_total = Label(self.frame10, text="Total Voltage", bg="#d0cee2", width=10, anchor="w")
        self.label_vpeizo_total.grid(column=1, row=3, columnspan=2)
        self.label12 = Label(self.frame10, bg="white", width=10)
        self.label12.grid(column=1, row=4, columnspan=2)

        # distance
        self.frame1 = LabelFrame(self.root, text="Distance (nm)", padx=10, pady=2, bg="gray", width=20)
        self.label1 = Label(self.frame1, bg="white", width=20)
        
        # current
        self.frame2 = LabelFrame(self.root, text="Current (nA)", padx=10, pady=2, bg="gray")
        self.label2 = Label(self.frame2, bg="white", width=20)
        
        # current setpoint
        self.frame3 = LabelFrame(self.root, text="Current Setpoint (nA)", padx=10, pady=2, bg="#ADD8E6")
        self.label3 = Entry(self.frame3, bg="white", width=24)
        self.label3.bind("<Return>", self.saveCurrentSetpoint)
        
        # current offset
        self.frame4 = LabelFrame(self.root, text="Current Offset (nA)", padx=10, pady=2, bg="#ADD8E6")
        self.label4 = Entry(self.frame4, bg="white", width=24)
        self.label4.bind("<Return>", self.saveCurrentOffset)
         
        # sample bias
        self.frame6 = LabelFrame(self.root, text="Sample Bias (V)", padx=10, pady=2, bg="#ADD8E6")
        self.label6 = Entry(self.frame6, bg="white", width=24)
        self.label6.bind("<Return>", self.saveSampleBias)

        # user notes text box
        self.frame7 = LabelFrame(self.root, text="NOTES", padx=10, pady=5, bg="#ADD8E6")
        self.label7 = Text(self.frame7, height=7, width=30)
        self.label8 = Text(self.frame7, height=1, width=8)
        self.label9 = Label(self.frame7, padx=10, text="Date:", height=1, width=5)

        # setup the drop option menu
        self.DropDownMenu()
        
        # optional graphic parameters
        self.padx = 20
        self.pady = 10
        
        # Initialize data attributes for continuous update
        self.distance = 0.0
        self.adc_curr = 0.0
        self.vpzo_down = 0
        self.vpzo_up = 0
        self.total_voltage = 0.0
        # self.update_label()
    
        # define images
        self.add_btn_image0 = ctk.CTkImage(Image.open("Images/Vpzo_Up_Btn.png"), size=(40,40))
        self.add_btn_image1 = ctk.CTkImage(Image.open("Images/Vpzo_Down_Btn.png"), size=(40,40))
        self.add_btn_image2 = ctk.CTkImage(Image.open("Images/Fine_Adjust_Btn_Up.png"), size=(40,40))
        self.add_btn_image3 = ctk.CTkImage(Image.open("Images/Fine_Adjust_Btn_Down.png"), size=(40,40))
        self.add_btn_image4 = ctk.CTkImage(Image.open("Images/Start_Btn.png"), size=(90,35))
        self.add_btn_image5 = ctk.CTkImage(Image.open("Images/Stop_Btn.png"), size=(90,35))
        self.add_btn_image6 = ctk.CTkImage(Image.open("Images/Acquire_IV.png"), size=(90,35))
        self.add_btn_image7 = ctk.CTkImage(Image.open("Images/Acquire_IZ.png"), size=(90,35))
        
        #self.led_frame = LabelFrame(self.root, text="", labelanchor= "s", padx=10, pady=5, bg="#eeeeee")
        self.add_btn_image8 = ctk.CTkImage(Image.open("Images/Stop_LED.png"), size=(35,35))
        self.add_btn_image9 = ctk.CTkImage(Image.open("Images/Start_LED.png"), size=(35,35))
        
        self.add_btn_image10 = ctk.CTkImage(Image.open("Images/Save_Home_Btn.png"), size=(90,35))
        self.add_btn_image11 = ctk.CTkImage(Image.open("Images/Return_Home_Btn.png"), size=(35,35))
        
        # create buttons with proper sizes															   
        self.start_btn = ctk.CTkButton(self.root, image=self.add_btn_image4, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.start_reading)
        self.stop_btn = ctk.CTkButton(self.root, image=self.add_btn_image5, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.stop_reading)
        self.acquire_iv_btn = ctk.CTkButton(self.root, image=self.add_btn_image6, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.open_iv_window)
        self.acquire_iz_btn = ctk.CTkButton(self.root, image=self.add_btn_image7, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.open_iz_window)
        self.save_home_pos = ctk.CTkButton(self.root, image=self.add_btn_image10, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.save_home)
        
        self.stop_led_btn = ctk.CTkLabel(self.root, image=self.add_btn_image8, text="", width=30, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0)
        self.start_led_btn = ctk.CTkLabel(self.root, image=self.add_btn_image9, text="", width=30, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0)
        
        self.return_to_home_frame = LabelFrame(self.root, text="Return Home", labelanchor= "s", padx=10, pady=5, bg="#eeeeee")
        self.return_to_home_pos = ctk.CTkButton(self.return_to_home_frame, image=self.add_btn_image11, text="", width=30, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.return_home)
        
        self.vpiezo_btn_frame = LabelFrame(self.root, text="Fine Adjust Tip", padx=10, pady=5, bg="#eeeeee")
        self.vpiezo_adjust_btn_up = ctk.CTkButton(master=self.vpiezo_btn_frame, image=self.add_btn_image0, text = "", width=40, height=40, compound="bottom", fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.piezo_inc)
        self.vpiezo_adjust_btn_down = ctk.CTkButton(master=self.vpiezo_btn_frame, image=self.add_btn_image1, text="", width=40, height=40, compound="bottom", fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.piezo_dec)
        
        self.fine_adjust_frame = LabelFrame(self.root, text="Stepper Motor", padx=10, pady=5, bg="#eeeeee")
        self.fine_adjust_btn_up = ctk.CTkButton(master=self.fine_adjust_frame, image=self.add_btn_image2, text = "", width=40, height=40, compound="bottom", fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.stepper_motor_up)
        self.fine_adjust_btn_down = ctk.CTkButton(master=self.fine_adjust_frame, image=self.add_btn_image3, text="", width=40, height=40, compound="bottom", fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.stepper_motor_down)

        # put on the grid all the elements
        self.publish()

    def publish(self):
        # positioning distance text box
        self.frame1.grid(row=11, column=4, padx=5, pady=5, sticky="sw")
        self.label1.grid(row=0, column=0, padx=5, pady=5)

        # positioning current text box
        self.frame2.grid(row=11, column=5, padx=5, pady=5, sticky="sw")
        self.label2.grid(row=0, column=1, padx=5, pady=5)   
        
        # positioning current setpoint text box
        self.frame3.grid(row=12, column=4, padx=5, pady=5, sticky="w")
        self.label3.grid(row=1, column=0, padx=5, pady=5) 
        
        # positioning current offset text box
        self.frame4.grid(row=12, column=5, padx=5, pady=5, sticky="w")
        self.label4.grid(row=1, column=1, padx=5, pady=5) 

        # positioning sample bias text box
        self.frame6.grid(row=13, column=5, padx=5, pady=5, sticky="nw")
        self.label6.grid(row=2, column=0, padx=5, pady=5) 

        # positioning the notes text box
        self.frame7.grid(row=11, column=7, rowspan=3, pady=5, sticky="n")
        self.label7.grid(row=1, column=0, pady=5, columnspan=3, rowspan=3) 
        self.label8.grid(row=0, column=2, pady=5, sticky="e")
        self.label9.grid(row=0, column=2, pady=5, sticky="w")

        # positioning the file drop-down menu
        self.drop_menu.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        '''
        Method to display all button widgets
        '''
        self.vpiezo_btn_frame.grid(row=8, column=0, rowspan=3, columnspan=2, padx=5, sticky="e")
        self.vpiezo_adjust_btn_up.grid(row=0, column=0)
        self.vpiezo_adjust_btn_down.grid(row=1, column=0)
        
        self.fine_adjust_frame.grid(row=11, column=0, rowspan=4, columnspan=2, padx=5, sticky="e")
        self.fine_adjust_btn_up.grid(row=0, column=0)
        self.fine_adjust_btn_down.grid(row=1, column=0)
        
        self.start_btn.grid(row=2, column=9, sticky="e")
        self.stop_btn.grid(row=3, column=9, sticky="ne")
        self.acquire_iv_btn.grid(row=4, column=9, sticky="ne")
        self.acquire_iz_btn.grid(row=5, column=9, sticky="ne")
        self.stop_led_btn.grid(row=2, column=10, sticky="e")

        # positioning for home and save home pos buttons
        self.save_home_pos.grid(row=8, column=9)
        
        self.return_to_home_frame.grid(row=9, column=9)
        self.return_to_home_pos.grid(row=0, column=0)

    def disable_widgets(self):
        '''
        Function to disable entry widgets when we start seeking
        Disabling:
            - vpzo delta
            - vpzo up
            - vpzo down
            - current setpoint
            - current offset
            - sample rate
            - stepper motor step size
            - stepper motor up
            - stepper motor down
            - vbias
        '''
        self.vpiezo_adjust_btn_down["state"] = "disabled"
        self.vpiezo_adjust_btn_up["state"] = "disabled"

    '''
    # send sample bias voltage to MCU
    def send_vbias(self): 
        #port = self.parent.serial_ctrl.serial_port
        port = self.parent.serial_ctrl.serial_port
        print(f"Port connected: {port}")
        
        sample_bias_float = self.get_float_value(self.label6, 1.0, "Voltage Bias")
        print(f"Saved sample bias value (float): {sample_bias_float}")
        
        #self.parent.ztm_serial.sendMsgA(self.port, ztmCMD.CMD_SET_VBIAS.value, ztmSTATUS.STATUS_DONE.value, 0, sample_bias_float,0)
    '''
      
    def open_iv_window(self):
        '''
        Method to open a new window when the "Acquire I-V" button is clicked
        '''
        new_window = ctk.CTkToplevel(self.root)
        IVWindow(new_window)

    def open_iz_window(self):
        '''
        Method to open a new window when the "Acquire I-Z" button is clicked
        '''
        port = self.parent.serial_ctrl.serial_port
        new_window = ctk.CTkToplevel(self.root)
        IZWindow(new_window, self.parent.serial_ctrl.serial_port)
    
    def startup_leds(self):
        '''
        Method to change the leds upon the user pressing the stop button
        '''
        self.stop_led_btn.grid_remove()
        self.start_led_btn.grid(row=2, column=10, sticky="e")
    
    def stop_leds(self):
        '''
        Method to change the leds upon the user pressing the stop button
        '''
        self.stop_led_btn.grid()
        self.start_led_btn.grid_remove()
       
    def start_reading(self):
        if self.check_connection():
            return
        else:
            print("ButtonGUI: Start button pressed")
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.startup_leds()
            self.parent.start_reading()			  
    
    def stop_reading(self):
        if self.check_connection():
            return
        else:
            print("ButtonGUI: Stop button pressed")
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.stop_leds()            
            # self.parent.stop_reading()

    '''
    Method to publish all widgets
    '''
    def publish(self):
        # positioning distance text box
        self.frame1.grid(row=11, column=4, padx=5, pady=5, sticky="sw")
        self.label1.grid(row=0, column=0, padx=5, pady=5)

        # positioning current text box
        self.frame2.grid(row=11, column=5, padx=5, pady=5, sticky="sw")
        self.label2.grid(row=0, column=1, padx=5, pady=5)   
        
        # positioning current setpoint text box
        self.frame3.grid(row=12, column=4, padx=5, pady=5, sticky="w")
        self.label3.grid(row=1, column=0, padx=5, pady=5) 
        
        # positioning current offset text box
        self.frame4.grid(row=12, column=5, padx=5, pady=5, sticky="w")
        self.label4.grid(row=1, column=1, padx=5, pady=5) 

        # positioning sample bias text box
        self.frame6.grid(row=13, column=5, padx=5, pady=5, sticky="nw")
        self.label6.grid(row=2, column=0, padx=5, pady=5) 

        # positioning the notes text box
        self.frame7.grid(row=11, column=7, rowspan=3, pady=5, sticky="n")
        self.label7.grid(row=1, column=0, pady=5, columnspan=3, rowspan=3) 
        self.label8.grid(row=0, column=2, pady=5, sticky="e")
        self.label9.grid(row=0, column=2, pady=5, sticky="w")

        # positioning the file drop-down menu
        #self.drop_menu.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # vpiezo tip fine adjust
        self.vpiezo_btn_frame.grid(row=8, column=0, rowspan=3, columnspan=2, padx=5, sticky="e")
        self.vpiezo_adjust_btn_up.grid(row=0, column=0)
        self.vpiezo_adjust_btn_down.grid(row=1, column=0)
        
        # stepper motor adjust
        self.fine_adjust_frame.grid(row=11, column=0, rowspan=4, columnspan=2, padx=5, sticky="e")
        self.fine_adjust_btn_up.grid(row=0, column=0)
        self.fine_adjust_btn_down.grid(row=1, column=0)
        
        # start/stop buttons
        self.start_btn.grid(row=2, column=9, sticky="e")
        self.stop_btn.grid(row=3, column=9, sticky="ne")
        
        # sweep windows buttons
        self.acquire_iv_btn.grid(row=4, column=9, sticky="ne")
        self.acquire_iz_btn.grid(row=5, column=9, sticky="ne")
        
        # led
        self.stop_led_btn.grid(row=2, column=10, sticky="e")

        # save home position
        self.save_home_pos.grid(row=8, column=9)
        
        # reset home position
        self.return_to_home_frame.grid(row=9, column=9)
        self.return_to_home_pos.grid(row=0, column=0)

    '''
    Function to send a message to the MCU and retry if we do
    not receive expected response
    '''
    def send_msg_retry(self, port, msg_type, cmd, status, status_response, *params, max_attempts=1, sleep_time=0.5):
        #global curr_data
        
        attempt = 0
        
        msg_print = [msg_type, cmd, status]
        
        # Convert each element in msg_print to a hex string
        msg_print_hex = ' '.join(format(x, '02X') for x in msg_print)
        
        print(f"\nMESSAGE BEING SENT: {msg_print_hex}")
        
        while attempt < max_attempts:
            print(f"\n========== ATTEMPT NUMBER: {attempt+1} ==========")
            if msg_type == MSG_A:
                self.parent.ztm_serial.sendMsgA(port, cmd, status, *params)
            elif msg_type == MSG_B:
                self.parent.ztm_serial.sendMsgB(port, cmd, status, *params)
            elif msg_type == MSG_C:
                self.parent.ztm_serial.sendMsgC(port, cmd, status, *params)
            elif msg_type == MSG_D:
                self.parent.ztm_serial.sendMsgD(port, cmd, status, *params)
            elif msg_type == MSG_E:
                self.parent.ztm_serial.sendMsgE(port, cmd, status, *params)
            else:
                raise ValueError(f"Unsupported message type: {msg_type}")
            
            # returns 11 bytes of payload FALSE or byte response
            testMsg = self.parent.serial_ctrl.ztmGetMsg(port)
            #testMsg = self.parent.serial_ctrl.read_bytes()
            
            testMsg_hex = [b for b in testMsg]
            
            print(f"Serial response: {testMsg_hex}")
            
            # returns false or different values
            # msgA returns current, vbias, vpzo
            # msgB returns FALSE
            # msgC returns FALSE or status byte
            # msgD returns FALSE or num full steps
            # msgE returns FALSE
            # msgF returns FFT current data and frequency
            #self.parent.ztm_serial.unpackRxMsg(testMsg)
            
            ### Unpack data and display on the GUI
            if testMsg:
                if testMsg_hex[2] == status_response and len(testMsg) == 11:
                    unpackResponse = self.parent.ztm_serial.unpackRxMsg(testMsg)
                    print(f"Received correct status response from MCU: {testMsg[2]}")
                    
                    if unpackResponse:
                        if testMsg_hex[2] == ztmSTATUS.STATUS_STEP_COUNT.value:
                            #total_steps = int(struct.unpack('f', bytes(testMsg[5:9]))[0], 4) #unpack bytes & convert
                            print(f"Received values\nStepper Position Total (1/8) Steps: {unpackResponse}")
                            
                            return unpackResponse
                            #return True
                        elif testMsg_hex[2] == ztmSTATUS.STATUS_MEASUREMENTS.value:
                            curr_data = round(struct.unpack('f', bytes(testMsg[3:7]))[0], 3) #unpack bytes & convert
                            cStr = str(curr_data)  # format as a string
                            print("Received values\n\tCurrent: " + cStr + " nA\n")
                                
                            vb_V = round(Convert.get_Vbias_float(struct.unpack('H',bytes(testMsg[7:9]))[0]), 3) #unpack bytes & convert
                            vbStr = str(vb_V)   # format as a string
                            print("\tVbias: " + vbStr + " V\n")
                                # vpiezo
                            vp_V = round(Convert.get_Vpiezo_float(struct.unpack('H',bytes(testMsg[9:11]))[0]), 3) #unpack bytes & convert
                            vpStr = str(vp_V)   # format as a string
                            print("\tVpiezo: " + vpStr + " V\n")
                            
                            return True
                    return True
                else:
                    print(f"ERROR. Wrong response recieved: {testMsg}")
                    print(f"Length of message received {len(testMsg)}")
                    print(f"\tReceived status: {testMsg[2]}")
                    print(f"\tExpected status: {status_response}")
                             
            else:
                print("ERROR. Failed to receive response from MCU.")

            time.sleep(sleep_time)
            attempt += 1

    
    '''
    Function to error check user inputs and update widget
    '''
    def get_float_value(self, label, default_value, value_name):
        try:
            value = float(label.get())
            #print(value)
        except ValueError:
            print(f"Invalid input for {value_name}. Using default value of {default_value}.")
            value = default_value
        return value  
    
    '''
    Function to send user-inputted parameters to MCU, sample bias, sample rate, sample
    size, current setpoint*
    ### WILL BE CHANGING ###
    
    This function consists of the tip approach algorithm and receiving periodic data
    once the tip approach algorithm successfully finishes
    '''        
    def start_seeking(self):
        # access global variables
        global curr_setpoint
        global curr_data
        
        global vbias_save
        global vbias_done_flag
        
        global sample_rate_save
        global sample_rate_done_flag
    
        global sample_size_save    
        global sample_size_done_flag
        
        global tip_app_total_steps
        global curr_pos_total_steps
        
        # local variable
        self.count = 0
        
        # inside of this function updates curr_pos_total_steps
        curr_pos_total_steps = self.send_msg_retry(self.parent.serial_ctrl.serial_port, MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value)
        
        if self.check_connection():
            return
        else:
            # inside of this function updates curr_pos_total_steps
            successMsg = self.send_msg_retry(self.parent.serial_ctrl.serial_port, MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value)
            if successMsg:
                print("Received current stepper position from MCU.")
            else:
                print("ERROR. Current position not received.")
                return
            
            # skip tip approach process
            if curr_pos_total_steps == home_pos_total_steps and home_pos_total_steps != None:
                print("We are at the correct position to begin data acquisition.")
                self.enable_periodics()

            # check if home pos != none and is valid
            # check curr position vs home pos
            # else return and tell user

            print("\n----------START SEEKING TUNNELING CURRENT----------")
            #self.label2.after(0, self.update_label)  # to move once we start receiving data
            #self.root.after(1000, self.parent.graph_gui.update_graph) # to move once we start receiving data
            
            # check for port connection
            port = self.parent.serial_ctrl.serial_port
                
            # Note: Disable entry widgets when seeking
            
            ########## WHEN USER PRESSES START BTN ##########
            # 1. Check if user values are set, if not set them to a default value (vpzo = 1, vbias = 1, ***current = 0.5)
            # 2. If user input values for vpzo, vbias, and sample rate are not set, send messages for user inputs to MCU
            # 3. a) Verify we have DONE msgs received from MCU (vpzo and vbias)
            # 3. b) If DONE msgs not rcvd, MCU will send RESEND status and GUI will resend until we have DONE from MCU
            
            # error check current setpoint
            try:
                curr_setpoint = float(curr_setpoint)
            except (TypeError, ValueError):
                curr_setpoint = 0.5     # set to default value
                print("Current setpoint set to default value.")
            print(f"Current setpoint: {curr_setpoint}")
            
            # error check sample bias
            if not vbias_done_flag:
                # get vbias value
                try:
                    vbias_save = float(vbias_save)      # check if there is a sample bias user input
                except (TypeError, ValueError):
                    vbias_save = 1.0                    # set to default value
                    print("Sample bias set to default value. Sending sample bias message to MCU.")
                
                # send samplel bias msg and retrieve done
                success = self.send_msg_retry(port, MSG_A, ztmCMD.CMD_SET_VBIAS.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 0, vbias_save, 0)
                
                if success:
                    vbias_done_flag = 1
                else:
                    vbias_done_flag = 0
            print(f"Sample bias: {vbias_save}")
            
            # error check sample rate
            if not sample_rate_done_flag:
                # get sample rate
                if sample_rate_save == None:
                    sample_rate_save = 25000    # set to default vaue
                    print("Sample rate set to default value. Sending sample rate message to MCU.")
                    
                # send sample rate msg and receive done
                success = self.send_msg_retry(port, MSG_B, ztmCMD.CMD_SET_ADC_SAMPLE_RATE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value,  sample_rate_save)
                
                if success:
                    sample_rate_done_flag = 1
                else:
                    sample_rate_done_flag = 0
            print(f"Sample rate: {sample_rate_save}")
            
            '''
            # error check sample size - CURRENTLY WORKING ON
            if not sample_size_done_flag:
                # get sample size value
                try:
                    sample_size_save = int(sample_size_save)      # check if there is a sample bias user input
                except (TypeError, ValueError):
                    sample_size_save = 100                    # set to default value
                    print("Sample size set to default value. Sending sample size message to MCU.")
                
                # send sample size msg and retrieve done
                success = self.send_msg_retry(port, MSG_B, ztmCMD.CMD_SET_SAMPLE_SIZE.value, ztmSTATUS.STATUS_CLR.value, sample_size_save)
                
                if success:
                    sample_size_done_flag = 1
                else:
                    sample_size_done_flag = 0
            print(f"Sample size: {sample_size_save}")
            '''
            
            # sample_size_save = 10 # for debugging purposes, delete later
            
            
            # 4. Once we have all DONE msgs, request data msg from GUI to MCU
            # 5. GUI waits to receive data
            # 6. a) GUI receives data from MCU (ADC current- possibly vbias, vpzo, and distance)
            # 6. b) Keep going until read current reaches current setpoint (if curr_data < curr_setpoint = keep reading)
            ######### NOTE: put in function for vpiezo/delta v error check and TIP APPROACH #########
            if vbias_done_flag and sample_rate_done_flag:
                print("\n********** ADD SEAN'S TIP-APPROACH HERE **********")

                # when completed, tip_approach_done_flag = 1
                    # BUT add a condition to check if the done flag already = 1
                # self.label2.after(0, self.update_label)  # to move here somewhere once we start receiving actual data
                # self.root.after(1000, self.parent.graph_gui.update_graph) # to move here somewhere once we start receiving actual data
                # move on to periodic data routine
                
                tip_app_total_steps = self.send_msg_retry(self.parent.serial_ctrl.serial_port, MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value)
                self.enable_periodics()

    '''
    Function to enable and read periodic data from the MCU
    '''
    def enable_periodics(self):
        count = 0
        measure_count = 0
        
        if self.check_connection():
            return
        else:
        ########## 
            print("\n********** BEGIN ENABLING PERIODIC DATA **********")
            
            # resets visual graph and data
            self.parent.graph_gui.reset_graph()
            # turns interactive graph on
            plt.ion()

            port = self.parent.serial_ctrl.serial_port
            
            #enable_data_success = self.parent.ztm_serial.sendMsgC(port, ztmCMD.CMD_PERIODIC_DATA_ENABLE, ztmSTATUS.STATUS_CLR)
            
            enable_data_success = self.send_msg_retry(port, MSG_C, ztmCMD.CMD_PERIODIC_DATA_ENABLE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value)
            
            if enable_data_success:
                print("Received DONE.")
                
                while count < 10:
                    response = self.parent.serial_ctrl.ztmGetMsg(port)
                    if response[2] == ztmSTATUS.STATUS_MEASUREMENTS.value:
                        print("Received MEASUREMENTS response.")
                        
                        curr_data = round(struct.unpack('f', bytes(response[3:7]))[0], 3) #unpack bytes & convert
                        cStr = str(curr_data)  # format as a string
                        print("Received values\n\tCurrent: " + cStr + " nA\n")
                    else:
                        print("Did not receive MEASUREMENTS response.")
                    
                    # use this to call _update_graph() everytime a data point is recieved.
                    self.adc_curr = curr_data
                    self.update_label()
                    self.parent.graph_gui.update_graph()
                    count +=1
                    #time.sleep(1.0)
            else:
                print("Did not receive DONE.")

            # turns interactive graph off
            plt.ioff()

                
    def savePiezoValue(self, event): 
        if self.check_connection():
            self.root.focus()
            return
        else:
            self.root.focus()
            
            vpzo_value = float(self.label10.get())
        
            if vpzo_value < float(0.003):
                vpzo_value = float(0.003)
                messagebox.showerror("Invalid Value", "Invalid input. Voltage is too small, defaulted to 3 mV.")
                
            print(f"Saved vpiezo value: {vpzo_value}")
            
            self.label12.configure(text=f"{0:.3f} ")
            self.label10.delete(0, END)
            self.label10.insert(0, str(vpzo_value))
        
    def piezo_inc(self):
        if self.check_connection():
            return
        else: 
            self.vpzo_up = 1
            self.sendPiezoAdjust()
    
    def piezo_dec(self):
        if self.check_connection():
            return
        else:
            self.vpzo_down = 1
            self.sendPiezoAdjust()
        
    '''
    Function to send total vpiezo to MCU
    '''
    def sendPiezoAdjust(self):
        if self.check_connection():
            return
        else:
            print("\n----------SENDING PIEZO ADJUST----------")
            port = self.parent.serial_ctrl.serial_port
            
            delta_v_float = self.get_float_value(self.label10, 1.0, "Piezo Voltage")
            
            if delta_v_float < float(0.003):
                delta_v_float = float(0.003)
            
            print(f"Saved delta V (float): {delta_v_float}")
            
            if 0 <= self.total_voltage <= 10:
                if self.vpzo_up:
                    if self.total_voltage + delta_v_float <= 10:
                        self.total_voltage += delta_v_float
                    else:
                        self.total_voltage = 10.000
                        InfoMsg = f"Total voltage exceeds 10 V. Maximum allowed is 10 V."
                        messagebox.showerror("INVALID", InfoMsg)
                        return
                        # send msg to MCU
                    self.vpzo_up = 0
                elif self.vpzo_down:
                    if self.total_voltage - delta_v_float >= 0:
                        self.total_voltage -= delta_v_float
                    else:
                        self.total_voltage = 0.000
                        InfoMsg = f"Total voltage below 0 V. Minimum allowed is 0 V."
                        messagebox.showerror("INVALID", InfoMsg)
                        return
                        # send msg to MCU
                    self.vpzo_down = 0
            else:
                InfoMsg = f"Invalid range. Stay within 0 - 10 V."
                messagebox.showerror("INVALID", InfoMsg)
                return
                # send msg to MCU
            
            print(f"Total Voltage: {self.total_voltage}")
            self.label12.configure(text=f"{self.total_voltage:.3f} ")
            
            success = self.send_msg_retry(port, MSG_A, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 0, 0, self.total_voltage)
            
            if success:
                print("\nSUCCESS. Received done message.")
            else:
                print("\nERROR. Failed to send piezo voltage.")
          
        
    '''
    Function to save the user inputted value of current setpoint to use for 
    the start seeking function
    
    QUESTION: Range for current setpoint?
    '''
    def saveCurrentSetpoint(self, _): 
        global curr_setpoint 
        
        if self.check_connection():
            self.root.focus()
            return
        else:
            try:
                curr_setpoint = float(self.label3.get())
                print(f"\nSaved current setpoint value: {curr_setpoint}")
            
                self.root.focus()
            except ValueError:
                self.root.focus()
                self.label3.delete(0,END)
                self.label3.insert(0,0.000)
                messagebox.showerror("Invalid Value", "Error. Please enter a valid input.")

    '''
    Save current offset and use to offset the graph
    
    QUESTION: Range for current offset?
    '''
    def saveCurrentOffset(self, event): 
        if self.check_connection():
            self.root.focus()
            return
        else:
            try:
                curr_offset = float(self.label4.get())
                print(f"\nSaved current offset value: {curr_offset}")
                self.root.focus()
            except ValueError:
                self.root.focus()
                self.label4.delete(0,END)
                self.label4.insert(0,0.000)
                messagebox.showerror("Invalid Value", "Error. Please enter a valid input.")

    '''
    Function to send vbias msg to the MCU and waits for a DONE response
    Check if DONE or ACK is expected
    - range of -10 V to 10 V
    '''
    def saveSampleBias(self, event): 
        if self.check_connection():
            self.root.focus()
            return
        else:
            self.root.focus()
            
            try:
                print("\n----------SENDING SAMPLE BIAS----------")
                port = self.parent.serial_ctrl.serial_port
                global vbias_save
                global vbias_done_flag
                
                vbias_save = self.get_float_value(self.label6, 1.0, "Voltage Bias")
                
                # error checking within range
                if vbias_save not in range(-10, 10):
                    self.label6.delete(0, END)
                    self.label6.insert(0, 0.000)
                    
                
                success = self.send_msg_retry(port, MSG_A, ztmCMD.CMD_SET_VBIAS.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 0, vbias_save, 0)
                
                print(f"Saved sample bias value (float): {vbias_save}")
                
                #vbias_done_flag = 1    # used for debugging - delete later
                
                if success:
                    print("Received done message.")
                    vbias_done_flag = 1
                else:
                    print("Failed to send vbias.")
                    vbias_done_flag = 0
                    
            except ValueError:
                pass
            
            
      
        

    '''
    Saves sample rate as an integer and sends that to the MCU
    '''
    def saveSampleRate(self, _):
        if self.check_connection():
            return
        else:
            global sample_rate_done_flag
            global sample_rate_save
            
            print("\n----------SENDING SAMPLE RATE----------")
            port = self.parent.serial_ctrl.serial_port
            
            if self.sample_rate_var.get() == "25 kHz":
                sample_rate_save = 25000
            elif self.sample_rate_var.get() == "12.5 kHz":
                sample_rate_save = 12500
            elif self.sample_rate_var.get() == "37.5 kHz":
                sample_rate_save = 37500
            elif self.sample_rate_var.get() == "10 kHz":
                sample_rate_save = 10000
            elif self.sample_rate_var.get() == "5 kHz":
                sample_rate_save = 5000
            print(f"Saved sample rate value: {sample_rate_save}")

            print(f"Sending cmd adjust sample rate to mcu for: {sample_rate_save}")
		
            #sample_rate_done_flag = 1      # debug start_seeking()
            
            success = self.send_msg_retry(port, MSG_B, ztmCMD.CMD_SET_ADC_SAMPLE_RATE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.VALUE, sample_rate_save)
            
        
            if success:
                print("Received done message.")
                sample_rate_done_flag = 1
            else:
                print("Failed to send sample rate.")
                sample_rate_done_flag = 0
                
    '''
    Send sample size as an integer and sends that to the MCU
    '''
    def sendSampleSize(self, _):
        global sample_size_save
        global sample_size_done_flag
        
        if self.check_connection():
            self.root.focus()
            return
        else:
            self.root.focus()
            
            print("\n----------SENDING SAMPLE SIZE----------")
            port = self.parent.serial_ctrl.serial_port
            
            try:
                sample_size_save = int(self.sample_size.get())
                if sample_size_save not in range(1, 1025):
                    if sample_size_save < 1:
                        sample_size_save = 1
                        messagebox.showerror("Invalid Value", "Invalid input. Sample size defaulted to 1.")
                    elif sample_size_save > 1024:
                        sample_size_save = 1024
                        messagebox.showerror("Invalid Value", "Invalid input. Sample size defaulted to 1024.")

                    sample_size_str = str(sample_size_save)
                    self.root.focus()
                    self.sample_size.delete(0, END)
                    self.sample_size.insert(0, sample_size_str)
                
                print(f"Saved sample size value: {sample_size_save}")

                print(f"Sending cmd adjust sample size to mcu for: {sample_size_save}")
                
                # Note: msg will be defined at a later time
                
                success = self.send_msg_retry(port, MSG_B, ztmCMD.CMD_SET_ADC_SAMPLE_SIZE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, sample_size_save)
                
            
                if success:
                    print("Received done message.")
                    #sample_size_done_flag = 1
                else:
                    print("Failed to send sample size.")
                    #sample_size_done_flag = 0
                
                
            except ValueError:
                self.root.focus()
                self.sample_size.delete(0, END)
                messagebox.showerror("Invalid Value", "Please enter a whole number from [1-1024].")
                        
    '''
    Saves adjust stepper motor step size as an integer 'fine_adjust_step_size' 
    '''
    def saveStepperMotorAdjust(self, _):
        if self.check_connection():
            return
        else:
            if self.fine_adjust_var.get() == "Full":
                self.fine_adjust_step_size = 0
                approx_step_distance = 0.008    # need to update
            elif self.fine_adjust_var.get() == "Half":
                self.fine_adjust_step_size = 1
                approx_step_distance = 0.004    # need to update
            elif self.fine_adjust_var.get() == "Quarter":
                self.fine_adjust_step_size = 2
                approx_step_distance = 0.002    # need to update
            elif self.fine_adjust_var.get() == "Eighth":
                self.fine_adjust_step_size = 3
                approx_step_distance = 0.001    # need to update
            
            # print confirmation to terminal
            print(f"Saved fine adjust step size: {self.fine_adjust_var.get()} : {self.fine_adjust_step_size}")

            # display approx distance per step size to user
            self.label5.configure(text=f"{approx_step_distance:.3f} nm")

    '''
    Handles the button click for the stepper motor up arrow 
    '''
    def stepper_motor_up(self):
        if self.check_connection():
            return
        else:
            self.step_up = 1
            self.step_down = 0
            self.sendStepperMotorAdjust()
    
    '''
    Handles the button click for the stepper motor down arrow 
    '''
    def stepper_motor_down(self):
        if self.check_connection():
            return
        else:
            self.step_up = 0
            self.step_down = 1
            self.sendStepperMotorAdjust()

    '''
    Sends stepper motor adjust msg to the MCU
    '''
    def sendStepperMotorAdjust(self):
        if self.check_connection():
            return
        else:
            port = self.parent.serial_ctrl.serial_port
            
            # fine adjust direction : direction = 0 for up, 1 for down
            if self.step_up:
                fine_adjust_dir = 0
                self.step_up    = 0 
                dir_name = "up direction"
            elif self.step_down:
                fine_adjust_dir = 1
                self.step_down  = 0
                dir_name = "down direction"
                
            print(f"\n----------SENDING STEPPER MOTOR {dir_name}----------")
                                                        
            # number of steps, hardcoded = 1, for fine adjust arrows
            num_of_steps = 1

            success = self.send_msg_retry(self.parent.serial_ctrl.serial_port, MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, self.fine_adjust_step_size, fine_adjust_dir, num_of_steps)
        
            if success:
                print("Received done message.")
            else:
                print("Failed to receive response from MCU.")

    '''
    Function to save the new home position, where the tip is at when the function is called
    '''
    def save_home(self):
        global home_pos_total_steps
        global curr_pos_total_steps

        if self.check_connection():
            return
        else:
            ("\n----------SETTING NEW HOME POSITION----------")
            save_home_pos = self.send_msg_retry(self.parent.serial_ctrl.serial_port, MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value)
            if save_home_pos:
                print("Received total step count position from MCU and saved new home position.")

                # curr_pos_total_steps is set in send_msg_retry(), we then set global variable home_pos_total_steps to save this as new home position
                home_pos_total_steps = curr_pos_total_steps
            else:
                print("Failed to receive response from MCU.")
    
    '''
    Function to return to the home position and send it to the MCU
    '''
    def return_home(self):
        global home_pos_total_steps
        global curr_pos_total_steps

        if self.check_connection():
            return
        else:
            # if a home position has not been set, error message and return from function
            if home_pos_total_steps == None:
                InfoMsg = f"No Home Position has been set."
                messagebox.showerror("INVALID", InfoMsg)
                return

            ("\n----------RETURN TO HOME POSITION----------")
            # request total step for stepper motor from MCU
            save_home_pos = self.send_msg_retry(self.parent.serial_ctrl.serial_port, MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value)
             
            if save_home_pos:
                print("Received current step count position from MCU.")
                
                # if home position is lower than the tip's current position
                if home_pos_total_steps > curr_pos_total_steps:
                    return_dir = 1 # down
                    num_of_steps = home_pos_total_steps - curr_pos_total_steps
                    print(f"Home position is lower than current position by {num_of_steps} (1/8) steps\n")

                    # send command to stepper motor for number of steps between current position and home position
                    success = self.send_msg_retry(self.parent.serial_ctrl.serial_port, MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 3, return_dir, num_of_steps)
                    if success:
                        print("Received done message.")
                    else:
                        print("Failed to receive response from MCU.")

                # if home position is higher than the tip's current position
                elif home_pos_total_steps < curr_pos_total_steps:
                    return_dir = 0 # up
                    num_of_steps = curr_pos_total_steps - home_pos_total_steps
                    print(f"Home position is higher than current position by {num_of_steps} (1/8) steps")

                    # send command to stepper motor for number of steps between current position and home position
                    success = self.send_msg_retry(self.parent.serial_ctrl.serial_port, MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, 3, return_dir, num_of_steps)
                    if success:
                        print("Received done message.")
                    else:
                        print("Failed to receive response from MCU.")

                elif home_pos_total_steps == curr_pos_total_steps:
                    print("Tip is already at home position.")
                
            else:
                print("Failed to receive response from MCU.")
    
    '''
    Function to check if there is a valid port connection
    '''
    def check_connection(self):
        port = self.parent.serial_ctrl.serial_port
        #print(f"{port}")   # debugging - delete later
        if port is None:
            InfoMsg = f"ERROR. Connect to COM PORT."
            messagebox.showerror("Connection Error", InfoMsg)
            return True
        else:
            return False

    def update_label(self):
        random_num = random.uniform(0, 5) 
        self.label2.configure(text=f"{self.adc_curr:.3f} nA")
        #self.label2.configure(text=f"{curr_data:.3f} nA") # swap this in one we start receiving data
        self.label1.configure(text=f"{self.distance:.3f} nm")
        self.label2.after(100, self.update_label)

    def get_current_label2(self):
        current_value = float(self.label2.cget("text").split()[0])  # assuming label2 text value is "value" nA
        return current_value
        
    '''
    Method to list all the File menu options in a drop menu
    '''
    def DropDownMenu(self):
        self.menubar = tk.Menu(self.root)
        
        #self.custom_font = tkFont.Font(size=8)
        
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Save", command=self.save_graph)
        self.filemenu.add_command(label="Save As", command=self.save_graph_as)
        self.filemenu.add_command(label="Export (.csv)", command=self.export_data)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.root.quit)
        
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        
        self.root.config(menu=self.menubar)
    
    def save_graph(self):
        '''
        Saves the current graph image with a default file name.
        '''
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        default_filename = os.path.join(downloads_folder, "current_graph.png")
        self.parent.graph_gui.fig.savefig(default_filename)
        messagebox.showinfo("Save Graph", f"Graph saved in Downloads as {default_filename}")

    def save_graph_as(self):
        '''
        Saves the current graph image with a user-specified file name.
        '''
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if file_path:
            self.parent.graph_gui.fig.savefig(file_path)
            messagebox.showinfo("Save Graph As", f"Graph saved as {file_path}")
    
    '''
    Handles the exporting of data collected into a .csv file
    ''' 
    def export_data(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Excel.CSV", "*.csv"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w', newline='') as file:
                header_text = self.label7.get(1.0, ctk.END)
                header_text = header_text.strip()
                header_date = self.label8.get(1.0, ctk.END)
                header_date = header_date.strip()

                # conjoining and formatting data
                headers = ["Time", "Tunneling Current (nA)"]
                data_to_export = [headers]
                data_to_export.extend(zip(self.parent.graph_gui.x_data, self.parent.graph_gui.y_data))

                # writing to file being created
                writer = csv.writer(file)
                writer.writerow(['Date:', header_date])
                writer.writerow(['Notes:',header_text])
                writer.writerows(data_to_export)

            messagebox.showinfo("Export Data", f"Data exported as {file_path}")
            
     
class GraphGUI:
    '''
    Function to initialize the data arrays and the graphical display
    ''' 
    def __init__(self, root, meas_gui):
        self.root = root
        self.meas_gui = meas_gui

        #configures plot
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Tunneling Current (nA)')
       
        # initializes graphical data
        self.y_data = []
        self.x_data = []
        self.line, = self.ax.plot([], [], 'r-')

        # Create a canvas to embed the figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=0, column=3, columnspan=6, rowspan=10, padx=10, pady=5)
    
    '''
    This will update the visual graph with the data points obtained during
    the Piezo Voltage Sweep. The data points are appended to the data arrays.
    '''
    def update_graph(self):
        # fetch data from label 2
        current_data = self.meas_gui.get_current_label2()
        
        # update data with next data points
        self.y_data.append(current_data)
        self.x_data.append(datetime.time)
        
        # update graph with new data
        self.line.set_data(self.x_data, self.y_data)
        self.ax.relim()

        # set x-axis parameters
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.xaxis.set_major_locator(mdates.SecondLocator(interval=2))
        # controls how much time is shown within the graph, currently displays the most recent 10 seconds
        self.ax.set_xlim(datetime.datetime.now() - datetime.timedelta(seconds=10), datetime.datetime.now())
        self.ax.autoscale_view()
        
        # redraw canvas
        self.canvas.draw()
        self.canvas.flush_events()

    '''
    Resets the visual graph and clears the data points.
    '''
    def reset_graph(self):
        self.ax.clear()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Tunneling Current (nA)')
        self.y_data = []
        self.x_data = []
        self.line, = self.ax.plot([], [], 'r-')
        self.canvas.draw()
        self.canvas.flush_events()
        
if __name__ == "__main__":
    root_gui = RootGUI()
    root_gui.root.mainloop()