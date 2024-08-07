from tkinter import Label, LabelFrame, Button, StringVar, OptionMenu, Entry, END, Text
from tkinter import messagebox 
from tkinter import filedialog
from PIL import Image
import customtkinter as ctk
import serial.tools.list_ports
import tkinter as tk
import serial
import os
import struct
import time
import queue
import csv
#import sys
import datetime
import threading
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
#import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# import other files
import globals
from IV_Window import IVWindow  # import the IV Window Class
from IZ_Window import IZWindow  # import the IV Window Class
from value_conversion import Convert
from ztmSerialCommLibrary import usbMsgFunctions, ztmCMD, ztmSTATUS
from SPI_Data_Ctrl import SerialCtrl

# global variables
curr_setpoint = 0.0

# for MCU sent measurements
curr_data = 0.0
vb_V = 0.0
vp_V = 0.0

vpiezo_dist = 0

vbias_save = None
vbias_done_flag = 0

# used for the tip approach
vpiezo_tip = 0.0
tunneling_steps = 0

sample_rate_save = None
sample_rate_done_flag = 0

sample_size_save = None
sample_size_done_flag = 0

home_pos_total_steps = None
curr_pos_total_steps = None

tip_app_total_steps = None

startup_flag = 0

TUNN_APPR_FLAG = 0
CAP_APPR_FLAG = 0
PERIODICS_FLAG = 0
STOP_BTN_FLAG = 0

###################################################################################################################
#                                                 RootGUI CLASS                                                   #
###################################################################################################################
class RootGUI:
    def __init__(self):
        """
        Initializes the main window and its components.
        """
        self.root = ctk.CTk()
        self.root.title("Homepage")
        self.root.config(bg="#eeeeee")
        self.root.geometry("1300x650")
        #self.root.resizable(False, False)
        
        # Add a method to quit the application
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
        
        # Initialize serial control
        self.serial_ctrl = SerialCtrl(None, 460800)
        self.ztm_serial = usbMsgFunctions(self)
					
        # Initialize other components
        self.meas_gui = MeasGUI(self.root, self)
        self.graph_gui = GraphGUI(self.root, self.meas_gui)
        self.com_gui = ComGUI(self.root, self)
        
    def quit_application(self):
        """
        Quits the application and closes the serial read thread.
        """
        #print("\nQUITTING APPLICATION")
        if self.serial_ctrl:
            self.serial_ctrl.stop()
        
        self.root.quit()
    
    def start_reading(self):
        """
        Opens the serial read thread and enables the start of periodic data reading.
        """
        #print("Starting to read data...")
        if self.serial_ctrl:
            #print("Serial controller is initialized, starting now...")
            if(TUNN_APPR_FLAG):
                self.meas_gui.tunneling_approach()
            elif(CAP_APPR_FLAG):
                self.meas_gui.cap_approach()
            elif(PERIODICS_FLAG):
                self.meas_gui.enable_periodics()
            self.serial_ctrl.running = True
        #else:
            #print("Serial controller is not initialized.")
    
    def stop_reading(self):
        """
        Disables the reading of periodic data in a background thread.
        """
        def stop_reading_task():
            # Clear buffer
            self.clear_buffer()
            
            start_time = time.time()
            success = self.meas_gui.send_msg_retry(self.serial_ctrl.serial_port, globals.MSG_C, ztmCMD.CMD_PERIODIC_DATA_DISABLE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value)

            while not success and (time.time() - start_time) < globals.TIMEOUT:
                success = self.meas_gui.send_msg_retry(self.serial_ctrl.serial_port, globals.MSG_C, ztmCMD.CMD_PERIODIC_DATA_DISABLE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value)
            
            if success:
                #print("Stopped reading data...")
                self.meas_gui.enable_widgets()
                self.meas_gui.stop_leds()
            #else:
                #print("Did not receive valid response within timeout period. Moving on.")


        # Run the stop reading task in a separate thread
        stop_thread = threading.Thread(target=stop_reading_task)
        stop_thread.start()
    
    def clear_buffer(self):
        """
        Clears the serial buffer to make room for other messages.
        """
        if self.serial_ctrl.serial_port.in_waiting > 0:
            #print(f"{self.serial_ctrl.serial_port.in_waiting} bytes are stuck in the buffer.")
            self.serial_ctrl.serial_port.read(self.serial_ctrl.serial_port.in_waiting)
            #print(f"{self.serial_ctrl.serial_port.in_waiting} bytes are stuck in the buffer.")
        #else:
            #print("No bytes stuck in the buffer.")

###################################################################################################################
#                                                 ComGUI CLASS                                                    #
###################################################################################################################
class ComGUI:
    def __init__(self, root, parent):
        """
        Initializes the communication manager interface.

        Args:
            root (tkinter.Tk): The root window of the application.
            parent (RootGUI): The parent class that manages the main application logic.
        """
        self.root = root
        self.parent = parent
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
        """
        Publishes the widgets for the communication manager.
        """
        self.frame.grid(row=1, column=0, rowspan=3, columnspan=3, padx=5, pady=5)
        self.label_com.grid(column=1, row=2)
        self.drop_com.grid(column=2, row=2, padx=self.padx)
        self.btn_refresh.grid(column=3, row=2, padx=self.padx)
        self.btn_connect.grid(column=3, row=3, padx=self.padx)

    def ComOptionMenu(self):
        """
        Gets the list of available COM ports and displays them in the application.
        """
        ports = serial.tools.list_ports.comports()
        self.serial_ports = [port.device for port in ports]
        self.clicked_com = StringVar()
        self.clicked_com.set("-" if self.serial_ports else "No COM port found")
        self.drop_com = OptionMenu(self.frame, self.clicked_com, *self.serial_ports, command=self.connect_ctrl)
        self.drop_com.config(width=10)
    
    def connect_ctrl(self, widget):
        """
        Determines the state of the connect button.
        """
        if self.clicked_com.get() == "-":
            self.btn_connect["state"] = "disabled"
        else:
            self.btn_connect["state"] = "active"

    def com_refresh(self):
        """
        Refreshes the list of available COMs.
        """
        #print("Refresh")
        self.drop_com.destroy()
        self.ComOptionMenu()
        self.drop_com.grid(column=2, row=2, padx=self.padx)
        logic = []
        self.connect_ctrl(logic)

    def serial_connect(self):
        """
        Verifies the connection of a port.
        """
        global startup_flag
        if self.btn_connect["text"] == "Connect":
            port = self.clicked_com.get()
            try:
                # Attempt to open the serial port to check if it is already in use
                test_serial = serial.Serial(port)
                test_serial.close()

                # If the port is available, proceed with the connection
                self.parent.serial_ctrl.port = port
                #print(f"Connecting to {port}...")
                
                serial_response = self.parent.serial_ctrl.start()

                if serial_response:
                    self.startup_routine()
                else:
                    self.btn_connect["text"] = "Connect"
                    self.btn_refresh["state"] = "active"
                    self.drop_com["state"] = "active"
                    InfoMsg = f"Failed to connect to {self.clicked_com.get()}."
                    messagebox.showerror("Connection Error", InfoMsg)
                    #print(f"Failed to connect to {port}.")
                    self.parent.serial_ctrl.running = False
                
                
            except serial.SerialException as e:
                self.btn_connect["text"] = "Connect"
                self.btn_refresh["state"] = "active"
                self.drop_com["state"] = "active"
                InfoMsg = f"Failed to connect to {self.clicked_com.get()}: {e}"
                messagebox.showerror("Connection Error", InfoMsg)
                #print(f"Failed to connect to {port}: {e}")
                self.parent.serial_ctrl.running = False
        else:
            if self.parent.serial_ctrl:
                self.parent.serial_ctrl.stop()
            self.btn_connect["text"] = "Connect"
            self.btn_refresh["state"] = "active"
            self.drop_com["state"] = "active"
            InfoMsg = f"UART connection using {self.clicked_com.get()} is now closed."
            messagebox.showwarning("Disconnected", InfoMsg)
            #print("\nDisconnected.")
            
            startup_flag = 0

    def startup_routine(self):
        """
        A message sent to the MCU upon valid connection of a port, starting the MCU program.
        """
        global startup_flag
        #print("*************** BEGINNING STARTUP ROUTINE ***************")
        port = self.parent.serial_ctrl.serial_port
        #print(f"{port}")
        # check for port connection
        #if port is None:
            #print("Port is not connected.")
        
        msg_response = self.parent.meas_gui.send_msg_retry(port, globals.MSG_C, ztmCMD.CMD_CLR.value, ztmSTATUS.STATUS_RDY.value, ztmSTATUS.STATUS_ACK.value)   
        
        if msg_response:
            #print("SUCCESS. Startup routine completed.")
            self.btn_connect["text"] = "Disconnect"
            self.btn_refresh["state"] = "disable"
            self.drop_com["state"] = "disable"
            InfoMsg = f"Successful UART connection using {self.clicked_com.get()}."
            messagebox.showinfo("Connected", InfoMsg)
            startup_flag = 1
        else:
            self.btn_connect["text"] = "Connect"
            self.btn_refresh["state"] = "active"
            self.drop_com["state"] = "active"
            InfoMsg = f"Failed to connect to {self.clicked_com.get()}."
            messagebox.showerror("Connection Error", InfoMsg)
            #print(f"Failed to connect to {self.clicked_com.get()}.")            
            #self.parent.serial_ctrl.running = False
            #print("ERROR. Failed to connect.")
            self.parent.serial_ctrl.running = False
            
            startup_flag = 0

###################################################################################################################
#                                                 MeasGUI CLASS                                                   #
###################################################################################################################
# class for measurements/text box widgets in homepage
class MeasGUI:
    def __init__(self, root, parent):
        """
        Initializes the widgets and logic for sending and receiving messages.

        Args:
            root (tkinter.Tk): The root window of the application
            parent (RootGUI): The parent class that manages the main application logic.
        """
        self.root = root
        self.parent = parent
        
        # Local variables for distnace and adc current readings
        self.distance   = 0.0
        self.adc_curr   = 0.0
        
        # Local variables for vpzo adjusting
        self.vpzo_down  = 0
        self.vpzo_up    = 0
        self.total_voltage = 0.0
        
        # Local variables for stepper motor adjusting
        self.step_up    = 0
        self.step_down  = 0


        '''    
        # Create a frame to hold the label and text box
        self.console_frame = ctk.CTkFrame(self.root, width=500, height=250)
        self.console_frame.grid(row=2, column=11, padx=20, pady=10, rowspan=13, sticky="nsew")

        # Create a label for the console panel
        self.console_label = ctk.CTkLabel(self.console_frame, text="Console Window", anchor="w", text_color="black", bg_color="#eeeeee")
        self.console_label.pack(fill="x", pady=(0, 5))

        # Create a text widget to serve as the console panel
        self.console_text = ctk.CTkTextbox(self.console_frame, height=500, width=250)
        self.console_text.pack(fill="both", expand=True)
        self.console_text.configure(state='disabled')

        # Set font size for the console text
        self.console_text.configure(font=("Helvetica", 10))  # Change font size as needed

        # Redirect stdout to the console text widget
        sys.stdout = self
        sys.stderr = self
        '''
        
        # Initialize measurement widgets
        self.initialize_widgets()
        self.update_label()

    def write(self, message):
        """
        Writes a message to the console text widget.

        Args:
            message (str): The message to be written to the console text widget.
        """
        self.console_text.configure(state='normal')
        self.console_text.insert(tk.END, message)
        self.console_text.see(tk.END)  # Scroll to the end
        self.console_text.configure(state='disabled')
        
    def initialize_widgets(self):
        """
        Initializes widgets needed for data.
        """
        # Optional graphic parameters
        self.padx = 20
        self.pady = 10
        
        # Sample rate drop-down list   ### ADJUST LATER
        self.frame8 = LabelFrame(self.root, text="", padx=5, pady=5, bg="#ADD8E6")
        self.label_sample_rate = Label(self.frame8, text="Sample Rate: ", bg="#ADD8E6", width=11, anchor="w")
        self.sample_rate_var = StringVar()
        self.sample_rate_var.set("-")
        self.sample_rate_menu = OptionMenu(self.frame8, self.sample_rate_var, "25 kHz", "12.5 kHz", "37.5 kHz", "10 kHz", "5 kHz", command=self.saveSampleRate)  
        self.sample_rate_menu.config(width=7)
        
        self.label_sample_rate.grid(column=1, row=1)
        self.sample_rate_menu.grid(column=2, row=1) 
        self.frame8.grid(row=13, column=4, padx=5, pady=5, sticky="")
        
        # Sample size user entry
        self.sample_size = Entry(self.frame8, width=13)
        self.sample_size_label = Label(self.frame8, text="Sample Size: ", bg="#ADD8E6", width=11, anchor="w")
        self.sample_size.bind("<Return>", self.saveSampleSize)
        
        self.sample_size.grid(column=2, row=2, pady=5)
        self.sample_size_label.grid(column=1, row=2)

        # Stepper motor adjust step size
        self.frame9 = LabelFrame(self.root, text="", padx=5, pady=5, bg="#ADD8E6")
        self.label_coarse_adjust = Label(self.frame9, text="Step Size: ", bg="#ADD8E6", width=8, anchor="w")
        self.coarse_adjust_var = StringVar()
        self.coarse_adjust_var.set("-")
        self.coarse_adjust_menu = OptionMenu(self.frame9, self.coarse_adjust_var, "Full", "Half", "Quarter", "Eighth", command=self.saveStepperMotorAdjust) 
        self.coarse_adjust_menu.config(width=6)

        self.label_coarse_adjust.grid(column=1, row=1)
        self.coarse_adjust_menu.grid(column=1, row=2) 
        self.frame9.grid(row=12, column=2, rowspan=2, columnspan=2, padx=5, pady=5, sticky="")
        self.label_coarse_adjust_inc = Label(self.frame9, text="Approx. Dist", bg="#ADD8E6", width=9, anchor="w")

        self.label5 = Label(self.frame9, bg="white", width=10)
        self.label_coarse_adjust_inc.grid(column=2, row=1)
        self.label5.grid(column=2, row=2, padx=5, pady=5)

        # Vpiezo adjust step size
        self.frame10 = LabelFrame(self.root, text="", padx=5, pady=5, bg="#d0cee2")
        self.label_vpeizo_delta = Label(self.frame10, text="Vpiezo ΔV (V):", bg="#d0cee2", width=11, anchor="w")
        self.label_vpeizo_delta.grid(column=1, row=1)
        self.frame10.grid(row=7, column=2, rowspan=4, columnspan=2, padx=5, pady=5, sticky="")
        
        ### ADJUST LATER
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

        # distance  ### ADJUST LATER
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
        self.label7.bind("<Return>", self.save_notes)
        
        self.label8 = Entry(self.frame7, width=10)
        self.label9 = Label(self.frame7, padx=10, text="Date:", height=1, width=5)
        self.label8.bind("<Return>", self.save_date)
    
        # define images
        self.add_btn_image0 = ctk.CTkImage(Image.open("Images/Vpzo_Up_Btn.png"), size=(40,40))
        self.add_btn_image1 = ctk.CTkImage(Image.open("Images/Vpzo_Down_Btn.png"), size=(40,40))
        self.add_btn_image2 = ctk.CTkImage(Image.open("Images/Fine_Adjust_Btn_Up.png"), size=(40,40))
        self.add_btn_image3 = ctk.CTkImage(Image.open("Images/Fine_Adjust_Btn_Down.png"), size=(40,40))
        #self.add_btn_image4 = ctk.CTkImage(Image.open("Images/Start_Btn.png"), size=(90,35))
        #self.add_btn_image5 = ctk.CTkImage(Image.open("Images/Stop_Btn.png"), size=(90,35))
        self.add_btn_image6 = ctk.CTkImage(Image.open("Images/Acquire_IV.png"), size=(90,35))
        self.add_btn_image7 = ctk.CTkImage(Image.open("Images/Acquire_IZ.png"), size=(90,35))
    
        self.add_btn_image8 = ctk.CTkImage(Image.open("Images/Stop_LED.png"), size=(35,35))
        self.add_btn_image9 = ctk.CTkImage(Image.open("Images/Start_LED.png"), size=(35,35))
        
        self.add_btn_image10 = ctk.CTkImage(Image.open("Images/Save_Home_Btn.png"), size=(90,35))
        self.add_btn_image11 = ctk.CTkImage(Image.open("Images/Return_Home_Btn.png"), size=(35,35))
        
        # create buttons with proper sizes															   
        self.start_stop_frame = LabelFrame(self.root, text="Start/Stop Processes", labelanchor="n", padx=10, pady=10, bg="#eeeeee")
        self.tip_approach_btn = ctk.CTkButton(self.start_stop_frame,text="Start Tip Approach", width=180, height=45, fg_color="#ff8000", text_color="black", bg_color="#eeeeee", corner_radius=10, command=self.start_tip_appr)
        self.cap_approach_btn = ctk.CTkButton(self.start_stop_frame,text="Start Capacitance Approach", width=90, height=45, fg_color="#ffff00", text_color="black", bg_color="#eeeeee", corner_radius=10, command=self.start_cap_appr)
        self.enable_periodics_btn = ctk.CTkButton(self.start_stop_frame, text="Start Periodic Data Transfer", width=90, height=45, fg_color="#00cc00", text_color="black", bg_color="#eeeeee", corner_radius=10, command=self.start_periodics)
        self.stop_btn = ctk.CTkButton(self.start_stop_frame, text="STOP", width=90, height=75, fg_color="#D51717", text_color="black", bg_color="#eeeeee", corner_radius=10, command=self.stop_reading)
        self.stop_led_btn = ctk.CTkLabel(self.start_stop_frame, image=self.add_btn_image8, text="", width=35, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0)
        self.start_led_btn = ctk.CTkLabel(self.start_stop_frame, image=self.add_btn_image9, text="", width=30, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0)
        
        # sweep windows frame and buttons
        self.sweep_windows_frame = LabelFrame(self.root, text="Sweep Windows", labelanchor="n", padx=10, pady=10, bg="#eeeeee")
        self.acquire_iv_btn = ctk.CTkButton(self.sweep_windows_frame, image=self.add_btn_image6, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.open_iv_window)
        self.acquire_iz_btn = ctk.CTkButton(self.sweep_windows_frame, image=self.add_btn_image7, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.open_iz_window)
        self.save_home_pos = ctk.CTkButton(self.root, image=self.add_btn_image10, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.save_home)
        
        # Return/save home position buttons
        self.return_to_home_frame = LabelFrame(self.root, text="Return Home", labelanchor= "s", padx=10, pady=5, bg="#eeeeee")
        self.return_to_home_pos = ctk.CTkButton(self.return_to_home_frame, image=self.add_btn_image11, text="", width=30, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.return_home)
        
        # Piezo adjust frame and buttons
        self.vpiezo_btn_frame = LabelFrame(self.root, text="Piezo Tip Adjust", padx=10, pady=5, bg="#eeeeee")
        self.vpiezo_adjust_btn_up = ctk.CTkButton(master=self.vpiezo_btn_frame, image=self.add_btn_image0, text = "", width=40, height=40, compound="bottom", fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.piezo_inc)
        self.vpiezo_adjust_btn_down = ctk.CTkButton(master=self.vpiezo_btn_frame, image=self.add_btn_image1, text="", width=40, height=40, compound="bottom", fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.piezo_dec)
        
        # Stepper motor adjust frame and buttons
        self.fine_adjust_frame = LabelFrame(self.root, text="Stepper Motor", padx=10, pady=5, bg="#eeeeee")
        self.fine_adjust_btn_up = ctk.CTkButton(master=self.fine_adjust_frame, image=self.add_btn_image2, text = "", width=40, height=40, compound="bottom", fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.stepper_motor_up)
        self.fine_adjust_btn_down = ctk.CTkButton(master=self.fine_adjust_frame, image=self.add_btn_image3, text="", width=40, height=40, compound="bottom", fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.stepper_motor_down)

        # setup the drop option menu
        self.DropDownMenu()
        
        # put on the grid all the elements
        self.publish()

    def disable_widgets(self):
        '''
        Function to disable entry widgets when we start seeking
        Disabling:
            - current setpoint
            - sample rate
            - stepper motor step size
            - stepper motor up
            - stepper motor down
            - iv window
            - iz window
            - reset home
            - save home
            - start btn
            - stop btn
        '''
        self.label3.configure(state="disabled")
        self.sample_rate_menu.configure(state="disabled")
        self.coarse_adjust_menu.configure(state="disabled")
        self.sample_size.configure(state="disabled")
        self.acquire_iv_btn.configure(state="disabled")
        self.acquire_iz_btn.configure(state="disabled")
        self.save_home_pos.configure(state="disabled")
        self.return_to_home_pos.configure(state="disabled")
        self.tip_approach_btn.configure(state="disabled")
        self.cap_approach_btn.configure(state="disabled")
        self.enable_periodics_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
    
    def enable_widgets(self):
        self.label3.configure(state="normal")
        self.sample_rate_menu.configure(state="normal")
        self.coarse_adjust_menu.configure(state="normal")
        self.sample_size.configure(state="normal")
        self.acquire_iv_btn.configure(state="normal")
        self.acquire_iz_btn.configure(state="normal")
        self.save_home_pos.configure(state="normal")
        self.return_to_home_pos.configure(state="normal")
        self.tip_approach_btn.configure(state="normal")
        self.cap_approach_btn.configure(state="normal")
        self.enable_periodics_btn.configure(state="normal")
        self.stop_btn.configure(state="disable")
      
    def open_iv_window(self):
        """
        Method to open the I-V Sweep window when the "Acquire I-V" button is clicked.
        """
        self.acquire_iz_btn["state"] = "disabled"
        port = self.parent.serial_ctrl.serial_port
        new_window = ctk.CTkToplevel(self.root)
        IVWindow(new_window, port)
        new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_closing(new_window))
        
        # Disable main window
        self.root.attributes("-disabled", True)

    def open_iz_window(self):
        """
        Method to open the I-Z Sweep window when the "Acquire I-Z" button is clicked.
        """
        self.acquire_iv_btn["state"] = "disabled"
        port = self.parent.serial_ctrl.serial_port
        new_window = ctk.CTkToplevel(self.root)
        IZWindow(new_window, port)
        new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_closing(new_window))
        
        # Disable main window
        self.root.attributes("-disabled", True)

    def on_closing(self, window):
        """
        Method to re-enable the main window when the IV or IZ window is closed.
        """
        window.destroy()
        self.root.attributes("-disabled", False)
        self.acquire_iv_btn["state"] = "normal"
        self.acquire_iz_btn["state"] = "normal"
        
    def startup_leds(self):
        """
        Method to change the LEDs upon the user pressing the start button.
        """
        self.stop_led_btn.grid_remove()
        self.start_led_btn.grid(row=3, column=10, sticky="e")
    
    def stop_leds(self):
        """
        Method to change the LEDs upon the user pressing the stop button.
        """
        self.stop_led_btn.grid()
        self.start_led_btn.grid_remove()

    def start_tip_appr(self):
        global TUNN_APPR_FLAG
        global CAP_APPR_FLAG
        global PERIODICS_FLAG

        TUNN_APPR_FLAG = 1
        CAP_APPR_FLAG = 0
        PERIODICS_FLAG = 0

        self.start_reading()

    def start_cap_appr(self):
        global TUNN_APPR_FLAG
        global CAP_APPR_FLAG
        global PERIODICS_FLAG

        TUNN_APPR_FLAG = 0
        CAP_APPR_FLAG = 1
        PERIODICS_FLAG = 0
        
        self.start_reading()

    def start_periodics(self):
        global TUNN_APPR_FLAG
        global CAP_APPR_FLAG
        global PERIODICS_FLAG

        TUNN_APPR_FLAG = 0
        CAP_APPR_FLAG = 0
        PERIODICS_FLAG = 1
        
        self.start_reading()

    def start_reading(self):
        """
        Initializes the data reading process when the start button is pressed.
        
        This method performs the following steps:
        1. Checks the connection status and if not connected exits out of the method.
        2. If connected, it prints a message and updates the button states.
        3. Calls the `startup_leds` method to change the LED status.
        4. Calls the parent's `start_reading` method in the RootGUI class to begin data reading.
        """
        global STOP_BTN_FLAG
        if self.check_connection():
            return
        else:
            #print("ButtonGUI: Start button pressed")
            STOP_BTN_FLAG = 0
            # will need to move this section so it only runs when we receive a valid response back
            self.parent.start_reading()			  
    
    def stop_reading(self):
        """
        Stops the data reading process when the stop button is pressed.
        
        This method performs the following steps:
        1. Checks the connection status and if not connected exits out of the method.
        2. If connected, it prints a message and updates the button states.
        3. Calls the `stop_leds` method to change the LED status.
        4. Calls the parent's `stop_reading` method in the RootGUI class to stop data reading.
        """
        global STOP_BTN_FLAG
        if self.check_connection():
            return
        else:
            #print("ButtonGUI: Stop button pressed")
            STOP_BTN_FLAG = 1
            self.parent.stop_reading()

    def publish(self):
        """
        Method to publish widgets in the MeasGUI class.
        """
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

        # vpiezo tip fine adjust
        self.vpiezo_btn_frame.grid(row=8, column=0, rowspan=3, columnspan=2, padx=5, sticky="e")
        self.vpiezo_adjust_btn_up.grid(row=0, column=0)
        self.vpiezo_adjust_btn_down.grid(row=1, column=0)
        
        # stepper motor adjust
        self.fine_adjust_frame.grid(row=11, column=0, rowspan=4, columnspan=2, padx=5, sticky="e")
        self.fine_adjust_btn_up.grid(row=0, column=0)
        self.fine_adjust_btn_down.grid(row=1, column=0)
        
        # start/stop buttons
        self.start_stop_frame.grid(row=3, column=9, columnspan=4)
        self.tip_approach_btn.grid(row=0, column=0, sticky="e")
        self.cap_approach_btn.grid(row=1, column=0, sticky="e")

        self.enable_periodics_btn.grid(row=2, column=0, sticky="e")
        self.stop_btn.grid(row=1, column=1, sticky="ne", padx=20, pady=10)
        # led
        self.stop_led_btn.grid(row=0, column=1, sticky="")

        # sweep windows buttons
        self.sweep_windows_frame.grid(row=8, column=10, rowspan=2)
        self.acquire_iv_btn.grid(row=0, column=0, sticky="")
        self.acquire_iz_btn.grid(row=1, column=0, sticky="")

        # save home position
        self.save_home_pos.grid(row=8, column=9)
        
        # reset home position
        self.return_to_home_frame.grid(row=9, column=9)
        self.return_to_home_pos.grid(row=0, column=0)

    
    def send_msg_retry(self, port, msg_type, cmd, status, status_response, *params, max_attempts=globals.MAX_ATTEMPTS, sleep_time=globals.TENTH_SECOND):
        """
        Function to send a message to the MCU and retry if we do
        not receive expected response.

        Args:
            port (_type_): _description_
            msg_type (_type_): _description_
            cmd (_type_): _description_
            status (_type_): _description_
            status_response (_type_): _description_
            max_attempts (int, optional): _description_. Defaults to 10.
            sleep_time (float, optional): _description_. Defaults to 0.5.

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """
        global curr_data
        global vb_V
        global vp_V
        global vpiezo_tip
        
        attempt = 0
        
        msg_print = [msg_type, cmd, status]
        
        # Convert each element in msg_print to a hex string
        msg_print_hex = ' '.join(format(x, '02X') for x in msg_print)
        
        #print(f"\nMESSAGE BEING SENT: {msg_print_hex}")
        
        while attempt < max_attempts:
            #print(f"\n========== ATTEMPT NUMBER: {attempt+1} ==========")
            if msg_type == globals.MSG_A:
                msg_response = self.parent.ztm_serial.sendMsgA(port, cmd, status, *params)
            elif msg_type == globals.MSG_B:
                msg_response = self.parent.ztm_serial.sendMsgB(port, cmd, status, *params)
            elif msg_type == globals.MSG_C:
                msg_response = self.parent.ztm_serial.sendMsgC(port, cmd, status)
            elif msg_type == globals.MSG_D:
                msg_response = self.parent.ztm_serial.sendMsgD(port, cmd, status, *params)
            elif msg_type == globals.MSG_E:
                msg_response = self.parent.ztm_serial.sendMsgE(port, *params)
            else:
                messagebox.showerror("ERROR", "Internal error. Please try again.")
            
            if msg_response:
                # returns 11 bytes of payload FALSE or byte response
                #testMsg = self.parent.serial_ctrl.ztmGetMsg()
                testMsg = self.parent.serial_ctrl.receive_serial()
                #print(f"Test msg: {testMsg}")
                
                ### Unpack data and display on the GUI
                if testMsg:
                    testMsg_hex = [b for b in testMsg]
                    #print(f"Serial response: {testMsg_hex}")
                    
                    # checks if status byte read is the same as status byte expected AND that the response is 11 bytes long
                    if testMsg_hex[2] == status_response and len(testMsg) == 11:
                        unpackResponse = self.parent.ztm_serial.unpackRxMsg(testMsg)
                        #print(f"Received correct status response from MCU: {testMsg[2]}")
                        
                        if isinstance(unpackResponse, tuple):
                            if len(unpackResponse) == 3:
                                if testMsg_hex[2] == ztmSTATUS.STATUS_MEASUREMENTS.value: #and testMsg_hex[1] == ztmCMD.CMD_PERIODIC_DATA_ENABLE.value:
                                    curr_data, vb_V, vp_V = unpackResponse
                                    
                                    #print(f"Received values\n\tCurrent: {curr_data} nA\n")
                                    #print(f"\tVbias: {vb_V} V\n")
                                    #print(f"\tVpiezo: {vp_V} V\n")
                                    
                                    vpiezo_tip = vp_V
                                    
                                    return True
                                #elif testMsg_hex[2] == ztmSTATUS.STATUS_MEASUREMENTS.value and testMsg_hex[1] == ztmCMD.CMD_REQ_DATA.value:
                                #    pass
                            #else:
                                #print("Unknown tuple response.")
                        else:
                            if testMsg_hex[2] == ztmSTATUS.STATUS_STEP_COUNT.value:
                                #print(f"Received values:\n\tStepper Position Total (1/8) Steps: {unpackResponse}")
                                return unpackResponse  
                        return True
                    
                    elif testMsg_hex[2] == ztmSTATUS.STATUS_NACK.value:
                        #print("NACK received.")
                        return
                    elif testMsg_hex[2] == ztmSTATUS.STATUS_FAIL.value:
                        #print("FAIL received.")
                        return
                    elif testMsg_hex[2] == ztmSTATUS.STATUS_RESEND.value:
                        #print("RESEND received. Resending message.")
                        return
                    # overcurrent(?)
                    elif testMsg_hex[2] == ztmSTATUS.STATUS_BUSY.value:
                        #print("BUSY received. Try again.")
                        return
                    elif testMsg_hex[2] == ztmSTATUS.STATUS_ERROR.value:
                        #print(f"Wrong message was sent.")
                        return 
                    else:
                        #print(f"ERROR. Wrong response recieved: {testMsg}")
                        #print(f"Length of message received {len(testMsg)}")
                        #print(f"\tReceived status: {testMsg[2]}")
                        #print(f"\tExpected status: {status_response}")
                        
                        if testMsg_hex[2] == ztmSTATUS.STATUS_MEASUREMENTS.value:
                            if cmd == ztmCMD.CMD_SET_VBIAS.value:
                                vb_V = round(Convert.get_Vbias_float(struct.unpack('H',bytes(testMsg[7:9]))[0]), 3) #unpack bytes & convert
                                vbStr = str(vb_V)   # format as a string
                                #print("\tVbias: " + vbStr + " V\n")
                                return vb_V
                            elif cmd == ztmCMD.CMD_PIEZO_ADJ.value:
                                # vpiezo
                                vp_V = round(Convert.get_Vpiezo_float(struct.unpack('H',bytes(testMsg[9:11]))[0]), 3) #unpack bytes & convert
                                vpStr = str(vp_V)   # format as a string
                                #print("\tVpiezo: " + vpStr + " V\n")
                                return vp_V
                #elif attempt == globals.MAX_ATTEMPTS:
                    #print("ERROR. Failed to receive a response from MCU.")
                #time.sleep(sleep_time)
                attempt += 1
                
            else:
                return False
    
    def sendMsgCapApproach(self, port, msg_type, cmd, status, status_response, *params, max_attempts=globals.MAX_ATTEMPTS, timeout=globals.TIMEOUT):
        """
        Function to send a message to the MCU and retry if we do
        not receive the expected response, using a timeout instead of a fixed sleep.

        Args:
            port (_type_): _description_
            msg_type (_type_): _description_
            cmd (_type_): _description_
            status (_type_): _description_
            status_response (_type_): _description_
            max_attempts (int, optional): _description_. Defaults to 10.
            timeout (float, optional): Timeout period for each attempt in seconds.

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """
        global curr_data
        global vb_V
        global vp_V
        global vpiezo_tip
        
        attempt = 0
        
        msg_print = [msg_type, cmd, status]
        
        # Convert each element in msg_print to a hex string
        msg_print_hex = ' '.join(format(x, '02X') for x in msg_print)
        
        #print(f"\nMESSAGE BEING SENT: {msg_print_hex}")
        
        while attempt < max_attempts:
            #print(f"\n========== ATTEMPT NUMBER: {attempt + 1} ==========")

            msg_response = self.parent.ztm_serial.sendMsgC(port, cmd, status)
            
            if msg_response:
                start_time = time.time()
                while (time.time() - start_time) < timeout:
                    # Check if data is available in the serial buffer
                    if self.parent.serial_ctrl.serial_port.in_waiting == 11:
                        testMsg = self.parent.serial_ctrl.ztmGetMsg()
                        #print(f"Test msg: {testMsg}")
                        
                        if testMsg:
                            testMsg_hex = [b for b in testMsg]
                            #print(f"Serial response: {testMsg_hex}")
                            
                            if testMsg_hex[2] == status_response and len(testMsg) == 11:
                                unpackResponse = self.parent.ztm_serial.unpackRxMsg(testMsg)
                                #print(f"Received correct status response from MCU: {testMsg[2]}")
                                
                                if isinstance(unpackResponse, tuple):
                                    if len(unpackResponse) == 2 and testMsg_hex[2] == ztmSTATUS.STATUS_FFT_DATA.value:
                                        fft_amp, fft_freq = unpackResponse
                                        #print(f"Received values\n\tFFT Amplitude: {fft_amp} nA")
                                        #print(f"\tFFT Frequency: {fft_freq} Hz\n")
                                        
                                        curr_data = fft_amp
                                        return fft_amp, fft_freq
                            #else:
                                #print(f"ERROR. Wrong response received: {testMsg}")
                                #print(f"Length of message received {len(testMsg)}")
                                #print(f"\tReceived status: {testMsg[2]}")
                                #print(f"\tExpected status: {status_response}")
                        
                        # Handle specific statuses
                        if testMsg_hex[2] == ztmSTATUS.STATUS_NACK.value:
                            #print("NACK received.")
                            return
                        elif testMsg_hex[2] == ztmSTATUS.STATUS_FAIL.value:
                            #print("FAIL received.")
                            return
                        elif testMsg_hex[2] == ztmSTATUS.STATUS_RESEND.value:
                            #print("RESEND received. Resending message.")
                            return
                        elif testMsg_hex[2] == ztmSTATUS.STATUS_BUSY.value:
                            #print("BUSY received. Try again.")
                            return
                        elif testMsg_hex[2] == ztmSTATUS.STATUS_ERROR.value:
                            #print(f"Wrong message was sent.")
                            return 
                
                # If no valid response within the timeout period
                #print("ERROR. Failed to receive a response within the timeout period.")
                attempt += 1
            else:
                return False
        return False
    
    def get_float_value(self, label, default_value, value_name):
        """
        Method to error check user inputs and update widget.

        Args:
            label (_type_): _description_
            default_value (_type_): _description_
            value_name (_type_): _description_

        Returns:
            _type_: [ADD DESCRIPTION HERE.]
        """
        try:
            value = float(label.get())
            #print(value)
        except ValueError:
            messagebox.showerror("Invalid Value", f"Invalid input for {value_name}. Using default value of {default_value}.")
            value = default_value
        return value  
    
############################################# TIP APPROACH #################################################
    def tunneling_approach(self):
        """
        @brief: This function looks for a desired tunneling current using the traditional algorithm
        @param targetCurrent_nA: The desired tunneling current the algorithm is looking for
        @retval: None
        """
        global STOP_BTN_FLAG
        global curr_setpoint
        global vpiezo_tip
        global tunneling_steps
        global curr_data
        global vb_V
        global vp_V
        
        if self.check_connection():
            return
        else:
        ##########    
            port = self.parent.serial_ctrl.serial_port
            
            if not self.saveCurrentSetpoint():
                return 
            
            # Set sample size to 24
            self.send_msg_retry(port, globals.MSG_B, ztmCMD.CMD_SET_ADC_SAMPLE_SIZE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, globals.TUNNELING_SAMPLE_SIZE)

            # Get a measurement from the MCU, send_msg_retry() will change the val of the global vars curr, vbias, vpzo
            success = self.send_msg_retry(port, globals.MSG_C, ztmCMD.CMD_REQ_DATA.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_MEASUREMENTS.value)
            
            if success:
                #print("\n----------BEGINNING TIP APPROACH ALGORITHM----------")
                # Resets visual graph and data
                self.parent.graph_gui.reset_graph()
                
                # Turns interactive graph on
                plt.ion()
                
                self.startup_leds()
                self.disable_widgets()
                
                while True:
                    if STOP_BTN_FLAG == 1:
                        plt.ioff()
                        break
                    
                    self.send_msg_retry(port, globals.MSG_C, ztmCMD.CMD_REQ_DATA.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_MEASUREMENTS.value)
                    
                    # Immediately step back and return if current >= target
                    if(curr_data >= curr_setpoint):
                        adjust_success = self.send_msg_retry(port, globals.MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, globals.EIGHTH_STEP, globals.DIR_DOWN, globals.NUM_STEPS)
                        if adjust_success:
                            #print("ADJUST SUCCESS.")
                            tunneling_steps -= globals.INC_EIGHT
                            plt.ioff()
                            return 1, curr_data, vb_V, vp_V, tunneling_steps
                        else:
                            #print("Did not receive correct response back.")
                            messagebox.showerror("ERROR", "Error. Unable to adjust the stepper motor.")
                    else:
                        # Update the graph with new data
                        self.parent.graph_gui.update_graph()
                        
                        vpiezo_tip, tunneling_steps = self.auto_move_tip(tunneling_steps, globals.APPROACH_STEP_SIZE_NM, globals.DIR_DOWN)

                    self.update_label()
                    self.parent.graph_gui.update_graph()
                STOP_BTN_FLAG = 0
            else:
                #print("Did not receive correct response back.")
                messagebox.showerror("ERROR", "Error. Did not receive correct response back.")
            
                # Turns interactive graph off
                plt.ioff()
            
    
    def auto_move_tip(self, steps, dist, dir):
        """
        @brief: This function changes the tip height using either the piezo or stepper motor.
        Note: If the distance is out of range for the piezo then the stepper motor will step up
        or down, and the new distance will not be exactly what was desired. This function was 
        created for the tunneling_approach function
        @param dist: The desired change in distance in nm
        @param dir: Direction for tip to move. Send "DOWN" to move tip down and "UP" to move tip up
        @retval: None
        """
        global vpiezo_tip
        
        port = self.parent.serial_ctrl.serial_port
        stepSet = False
        piezoSet = False
        delta_V = dist / globals.PIEZO_EXTN_RATIO
        
        # MOVING DOWN
        if(dir == globals.DIR_DOWN):
            # Piezo is fully extended, so we retract the tip and step the motor down
            if(vpiezo_tip + delta_V > globals.VPIEZO_APPROACH_MAX):
                vpiezo_tip = self.piezo_full_retract()
                # Move stepper motor DOWN an eighth step
                while(stepSet == False):
                    stepSet = self.send_msg_retry(port, globals.MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, globals.EIGHTH_STEP, globals.DIR_DOWN, globals.NUM_STEPS)
                # Increment number of steps 
                steps += globals.INC_EIGHT
            # Increment the piezo voltage by delta_V to step it down
            else:
                vpiezo_tip += delta_V
                # Send message to update vpiezo
                while(piezoSet == False):
                    piezoSet = self.send_msg_retry(port, globals.MSG_A, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 0, 0, vpiezo_tip)
        ########################################################################
        # MOVING UP
        else:
            if(vpiezo_tip - delta_V < globals.VPIEZO_APPROACH_MIN):
            # Piezo is fully retracted, so we extend the tip and step the motor up
            # Place the tip in approximately the same position
                # Move stepper motor UP an eighth step    
                while(stepSet == False):
                    stepSet = self.send_msg_retry(port, globals.MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, globals.EIGHTH_STEP, globals.DIR_UP, globals.NUM_STEPS)
                # Decrement number of steps 
                steps -= globals.INC_EIGHT
                vpiezo_tip = self.piezo_full_extend()
            else:
                vpiezo_tip -= delta_V
                # Send message to update vpiezo
                while(piezoSet == False):
                    piezoSet = self.send_msg_retry(port, globals.MSG_A, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 0, 0, vpiezo_tip)
        #print(f"\nNew vpiezo for tip approach: {vpiezo_tip} V\nStep Count: {steps}")
        return vpiezo_tip, steps
                
    def piezo_full_extend(self):
        """
        This function adjusts the tip down in increments instead of one total distance.

        Args:
            vpiezo (_type_): _description_
        """
        global vpiezo_tip

        #print("Piezo is extending...")
        
        port = self.parent.serial_ctrl.serial_port
        piezoSet = False
        # Extend piezo in small increments
        piezoStep = vpiezo_tip / 32
        while (vpiezo_tip != globals.VPIEZO_APPROACH_MAX):
            if vpiezo_tip < globals.VPIEZO_APPROACH_MAX:
                vpiezo_tip += piezoStep
            elif vpiezo_tip > globals.VPIEZO_APPROACH_MAX:
                vpiezo_tip = globals.VPIEZO_APPROACH_MAX
            while(piezoSet == False):
                piezoSet = self.send_msg_retry(port, globals.MSG_A, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 0, 0, vpiezo_tip)
        return vpiezo_tip
    
    def piezo_full_retract(self):
        """
        This function adjusts the tip up in increments instead of one total distasnce.

        Args:
            vpiezo (_type_): _description_
        """
        global vpiezo_tip
        
        #print("Piezo is retracting...")
        
        port = self.parent.serial_ctrl.serial_port
        piezoSet = False
        # Retract piezo in small increments
        piezoStep = vpiezo_tip / 32
        while (vpiezo_tip != globals.VPIEZO_APPROACH_MIN):
            if vpiezo_tip > globals.VPIEZO_APPROACH_MIN:
                vpiezo_tip -= piezoStep
            elif vpiezo_tip < globals.VPIEZO_APPROACH_MIN:
                vpiezo_tip = globals.VPIEZO_APPROACH_MIN
            while(piezoSet == False):
                piezoSet = self.send_msg_retry(port, globals.MSG_A, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 0, 0, vpiezo_tip)
        return vpiezo_tip

    def cap_approach(self):
        """
        @brief: This function gets the tip close to the sample by using the displacement current
        between the tip and the sample. It looks at the difference between the present displacement
        current and a previous displacement current. It uses a circular buffer to store the delayed
        displacement currents.

        @retval: None
        """
        global STOP_BTN_FLAG
        
        delay_line = [0] * (globals.DELAY_LINE_LEN + 1) # Initialize delay_line with zeros
        port = self.parent.serial_ctrl.serial_port
        
        # Start Sinusoidal Vbias
        success = self.send_msg_retry(port, globals.MSG_E, ztmCMD.CMD_VBIAS_SET_SINE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, globals.CAP_APPROACH_AMPL, globals.CAP_APPROACH_FREQ)
        
        if success:
            #print("\n----------BEGINNING CAP APPROACH ALGORITHM----------")
            # Resets visual graph and data
            self.parent.graph_gui.reset_graph()
            
            # Turns interactive graph on
            plt.ion()
            self.startup_leds()
            self.disable_widgets()
            
            # Get first fft measurement
            fft_meas = self.get_fft_peak()
            if fft_meas is None:
                #print("ERROR. Unable to start cap approach due to invalid FFT measurements.")
                return
            
            for i in range(globals.DELAY_LINE_LEN + 1): delay_line[i] = fft_meas
            notDone = 1
            fft_count = 0
            peaks = [0] * globals.FFT_AVG_LENGTH # Initialize peaks list
            detector_count = 0
            delay_index = 0
            
            while(notDone):
                if STOP_BTN_FLAG == 1:
                    plt.ioff()
                    break
                
                # Measure fft peak
                peaks[fft_count] = self.get_fft_peak()

                if(fft_count >= globals.FFT_AVG_LENGTH-1):
                    fft_meas = self.get_avg_meas(peaks)
                    delay_line[delay_index] = fft_meas # Store the new displacement current

                    # Increments index of circular buffer
                    delay_index = (delay_index + 1) % (globals.DELAY_LINE_LEN+1) 

                    # takes difference between the new current and the current 
                    diff = fft_meas - delay_line[delay_index] 
                    if(diff > globals.CRIT_CAP_SLOPE):
                        detector_count += 1
                        if(detector_count >= 3):
                            notDone = 0
                        else:
                            notDone = 1
                    else:
                        detector_count = 0
                        notDone = 1
                        success_move = self.send_msg_retry(port, globals.MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, globals.EIGHTH_STEP, globals.DIR_DOWN, globals.CAP_APPROACH_NUM_STEPS)
                        #if success_move:
                            #print("SUCCESS. Stepper motor moved in cap approach.")
                        #else:
                            #print("ERROR. Stepper motor failed to move in capacitance approach.")
                    self.update_label()
                    self.parent.graph_gui.update_graph()
                else:
                    fft_count = fft_count + 1
            STOP_BTN_FLAG = 0    
            plt.ioff()
            self.stop_leds()
            self.enable_widgets()
            self.parent.clear_buffer()
            success_stop_vbias = self.send_msg_retry(port, globals.MSG_C, ztmCMD.CMD_VBIAS_STOP_SINE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value)
            #if success_stop_vbias:
                #print("SUCCESS. Sinusoidal vbias has stopped.")
            #else:
                #print("ERROR. Sinusoidal vbias failed to stop.")
                
    def get_fft_peak(self):
        """
        [ADD DESCRIPTION HERE.]

        Returns:
            _type_: _description_
        """
        port = self.parent.serial_ctrl.serial_port
        
        result = self.sendMsgCapApproach(port, globals.MSG_C, ztmCMD.CMD_REQ_FFT_DATA.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_FFT_DATA.value)
        if result is None:
            #print("ERROR. Failed to retrieve FFT data.")
            return None
        else:
            peak, _ = result
            return peak
    
    def get_avg_meas(self, measurements):
        """
        [ADD DESCRIPTION HERE.]

        Args:
            measurements (_type_): _description_

        Returns:
            _type_: _description_
        """
        
        total = 0
        count = 0

        for measurement in measurements:
            if measurement is not None:
                total += measurement # Sum the first element of each tuple
                count += 1

        if count == 0:
            return None  # Return None if no valid measurements were found

        avg = total / count
        return avg
        '''
        sum = 0
        for i in range(len(measurements)): sum += measurements[i]
        sum /= len(measurements)
        return sum
        '''

    '''
    def tip_approach(self):
        """
        Function to send user-inputted parameters to MCU, sample bias, sample rate, sample
        size, current setpoint*
        ### WILL BE CHANGING ###
        
        This function consists of the tip approach algorithm and receiving periodic data
        once the tip approach algorithm successfully finishes.
        """
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
        curr_pos_total_steps = self.send_msg_retry(self.parent.serial_ctrl.serial_port, globals.MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value)
        
        if self.check_connection():
            return
        if tip_app_total_steps == curr_pos_total_steps:
                self.enable_periodics()
        else:
            #print("\n----------BEGINNING TIP APPROACH ALGORITHM----------")
            
            # check for port connection
            port = self.parent.serial_ctrl.serial_port
                
            # Note: Disable entry widgets when seeking
            
            ########## WHEN USER PRESSES START BTN ##########
            # 1. Check if user values are set, if not set them to a default value (vpzo = 1, vbias = 1, ***current = 0.5)
            # 2. If user input values for vpzo, vbias, and sample rate are not set, send messages for user inputs to MCU
            # 3. a) Verify we have DONE msgs received from MCU (vpzo and vbias)
            # 3. b) If DONE msgs not rcvd, MCU will send RESEND status and GUI will resend until we have DONE from MCU
            
            # NOT NEEDED ANYMORE(?)
            # error check current setpoint
            try:
                curr_setpoint = float(curr_setpoint)
            except (TypeError, ValueError):
                curr_setpoint = 0.5     # set to default value
                #print("Current setpoint set to default value.")
            #print(f"Current setpoint: {curr_setpoint}")
            
            # error check sample bias
            if not vbias_done_flag:
                # get vbias value
                try:
                    vbias_save = float(vbias_save)      # check if there is a sample bias user input
                except (TypeError, ValueError):
                    vbias_save = 1.0                    # set to default value
                    #print("Sample bias set to default value. Sending sample bias message to MCU.")
                
                # send samplel bias msg and retrieve done
                success = self.send_msg_retry(port, MSG_A, ztmCMD.CMD_SET_VBIAS.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 0, vbias_save, 0)
                
                if success:
                    vbias_done_flag = 1
                else:
                    vbias_done_flag = 0
            #print(f"Sample bias: {vbias_save}")
            
            # error check sample rate
            if not sample_rate_done_flag:
                # get sample rate
                if sample_rate_save == None:
                    sample_rate_save = 25000    # set to default vaue
                    #print("Sample rate set to default value. Sending sample rate message to MCU.")
                    
                # send sample rate msg and receive done
                success = self.send_msg_retry(port, MSG_B, ztmCMD.CMD_SET_ADC_SAMPLE_RATE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value,  sample_rate_save)
                
                if success:
                    sample_rate_done_flag = 1
                else:
                    sample_rate_done_flag = 0
            #print(f"Sample rate: {sample_rate_save}")
            
            
            # error check sample size - CURRENTLY WORKING ON
            if not sample_size_done_flag:
                # get sample size value
                try:
                    sample_size_save = int(sample_size_save)      # check if there is a sample bias user input
                except (TypeError, ValueError):
                    sample_size_save = int(100)                    # set to default value
                    #print("Sample size set to default value. Sending sample size message to MCU.")
                
                # send sample size msg and retrieve done
                success = self.send_msg_retry(port, MSG_B, ztmCMD.CMD_SET_ADC_SAMPLE_SIZE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, sample_size_save)
                
                if success:
                    sample_size_done_flag = 1
                else:
                    sample_size_done_flag = 0
            #print(f"Sample size: {sample_size_save}") 
            
            # sample_size_save = 10 # for debugging purposes, delete later
            
            
            # 4. Once we have all DONE msgs, request data msg from GUI to MCU
            # 5. GUI waits to receive data
            # 6. a) GUI receives data from MCU (ADC current- possibly vbias, vpzo, and distance)
            # 6. b) Keep going until read current reaches current setpoint (if curr_data < curr_setpoint = keep reading)
            ######### NOTE: put in function for vpiezo/delta v error check and TIP APPROACH #########
            if vbias_done_flag and sample_rate_done_flag and sample_size_done_flag:
                #print("\n********** ADD SEAN'S TIP-APPROACH HERE **********")

                # when completed, tip_approach_done_flag = 1
                    # BUT add a condition to check if the done flag already = 1
                # move on to periodic data routine
                
                tip_app_total_steps = self.send_msg_retry(self.parent.serial_ctrl.serial_port, globals.MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value)
                self.enable_periodics()
    '''
    
    def enable_periodics(self):
        """
        Function to enable and read periodic data from the MCU.
        NOTE: need to add a flag for checking tunneling approach
        """
        global STOP_BTN_FLAG
        global curr_data
        
        if self.check_connection():
            return
        else:
        ########## 
            port = self.parent.serial_ctrl.serial_port
            
            enable_data_success = self.send_msg_retry(port, globals.MSG_C, ztmCMD.CMD_PERIODIC_DATA_ENABLE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value)
            
            if enable_data_success:
                #print("\n********** BEGIN ENABLING PERIODIC DATA **********")
                #print("Received DONE.")
                # Resets visual graph and data
                self.parent.graph_gui.reset_graph() 
                # Turns interactive graph on
                plt.ion()
                
                self.startup_leds()
                self.disable_widgets()
                
                while True:
                    if STOP_BTN_FLAG == 1:
                        plt.ioff()
                        break
                    
                    response = self.parent.serial_ctrl.ztmGetMsg()
                    if response:
                        if response[2] == ztmSTATUS.STATUS_MEASUREMENTS.value or response[2] == ztmSTATUS.STATUS_ACK.value:
                            #print(f"Received correct response: {response[2]}")
                            
                            curr_data = round(struct.unpack('f', bytes(response[3:7]))[0], 3) 
                            cStr = str(curr_data) 
                            #print("Received values\n\tCurrent: " + cStr + " nA\n")
                        #else:
                            #print(f"Did not receive correct response: {response[2]}")
                    
                    # Use this to call update_graph() everytime a data point is recieved
                    self.adc_curr = curr_data
                    self.update_label()
                    self.parent.graph_gui.update_graph()
                STOP_BTN_FLAG = 0    
            else:
                #print("Did not receive DONE.")
                messagebox.showerror("ERROR.", "Failed to enable periodic data. Try again.")

            # Turns interactive graph off
            plt.ioff()      
             
    def savePiezoValue(self, _=None):         
        """
        Method to save the piezo voltage delta value; the
        value cannot be less than 3 mV.

        Args:
            event (_type_): [ADD DESCRIPTION HERE.]
        """
        if self.check_connection():
            self.root.focus()
            return
        else:
            self.root.focus()
            
            vpzo_value = self.get_float_value(self.label10, 1.0, "Piezo Voltage")
        
            if vpzo_value < globals.VPIEZO_DELTA_MIN:
                vpzo_value = globals.VPIEZO_DELTA_MIN
                messagebox.showerror("Invalid Value", "Invalid input. Voltage is too small, defaulted to 3 mV.")
                
            #print(f"Saved vpiezo value: {vpzo_value}")
            
            self.label12.configure(text=f"{0:.3f} ")
            self.label10.delete(0, END)
            self.label10.insert(0, str(vpzo_value))
        
    def piezo_inc(self):
        """
        Method to identify that the up arrow was pressed for Vpzo.
        """
        if self.check_connection():
            return
        else: 
            self.vpzo_up = 1
            self.vpzo_down = 0
            self.sendPiezoAdjust()
    
    def piezo_dec(self):
        """
        Method to identify that the down arrow was pressed for Vpzo.
        """
        if self.check_connection():
            return
        else:
            self.vpzo_down = 1
            self.vpzo_up = 0
            self.sendPiezoAdjust()
        
    def sendPiezoAdjust(self):
        """
        Method to send total piezo voltage to MCU, with a valid range
        of 0 to 10 V.
        """
        if self.check_connection():
            return
        else:
            #print("\n----------SENDING PIEZO ADJUST----------")
                
            port = self.parent.serial_ctrl.serial_port
            
            delta_v_float = self.get_float_value(self.label10, 1.0, "Piezo Voltage")
            
            #print(f"Saved delta V: {delta_v_float} V")
            
            if globals.VPIEZO_MIN <= self.total_voltage <= globals.VPIEZO_MAX:
                if self.vpzo_up:
                    if self.total_voltage + delta_v_float <= globals.VPIEZO_MAX:
                        self.total_voltage += delta_v_float
                    else:
                        self.total_voltage = globals.VPIEZO_MAX
                        messagebox.showerror("INVALID", "Total voltage exceeds 10 V. Maximum allowed is 10 V.")
                        return
                        # send msg to MCU
                    self.vpzo_up = 0
                elif self.vpzo_down:
                    if self.total_voltage - delta_v_float >= globals.VPIEZO_MIN:
                        self.total_voltage -= delta_v_float
                    else:
                        self.total_voltage = globals.VPIEZO_MIN
                        messagebox.showerror("INVALID", "Total voltage is below 0 V. Minimum allowed is 0 V.")
                        return
                    self.vpzo_down = 0
            else:
                messagebox.showerror("INVALID", "Invalid range. Stay within 0 - 10 V.")
                return

            # Clear buffer
            self.parent.clear_buffer()
                
            start_time = time.time()
            success = self.send_msg_retry(port, globals.MSG_A, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 0, 0, self.total_voltage)

            while not success and (time.time() - start_time) < globals.TIMEOUT:
                success = self.send_msg_retry(port, globals.MSG_A, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 0, 0, self.total_voltage)
            
            if isinstance(success, bool):       # if we received a DONE msg
                if success:
                    #messagebox.showinfo("Information", "SUCCESS. DONE received within timeout period.")
                    self.label12.configure(text=f"{self.total_voltage:.3f} ")
                    return
                else:
                    messagebox.showinfo("Information", "Did not process change in value within timeout period. Please try again.")
            elif isinstance(success, float):    # if we received a MEASUREMENT msg
                # Clear buffer
                self.parent.clear_buffer()
                
                # Get msg
                testMsg = self.parent.serial_ctrl.ztmGetMsg()

                # Unpack new vpzo value
                _, _, vpzo_new = self.parent.ztm_serial.unpackRxMsg(testMsg)
                
                if abs(vpzo_new - self.total_voltage) <= 0.05 * self.total_voltage:
                    #messagebox.showinfo("Information", "SUCCESS. Processed changed in value within timeout period.")
                    self.label12.configure(text=f"{self.total_voltage:.3f} ")
                    return
                else:
                    messagebox.showinfo("Information", f"Did not process change in value within {globals.TIMEOUT} period. Please try again.")
                    #print("Not received.")
                
    def saveCurrentSetpoint(self, _=None): 
        """
        Function to save the user inputted value of current setpoint to use for 
        the tip approach algorithm.
        QUESTION: Range for current setpoint?

        Args:
            _ (_type_): [ADD DESCRIPTION HERE.]
        """
        global curr_setpoint 
        
        self.root.focus()
        if self.check_connection():
            return
        else:
            try:
                curr_setpoint = float(self.label3.get())
                if 0.1 <= curr_setpoint <= 10:
                    #print(f"\nSaved current setpoint value: {curr_setpoint} nA")
                    return True
                else:
                    self.label3.delete(0,END)
                    self.label3.insert(0,0.000)
                    messagebox.showerror("Invalid Value", "Error. Please enter a valid current setpoint value.")
                    return False
            except ValueError:
                self.label3.delete(0,END)
                self.label3.insert(0,0.000)
                messagebox.showerror("Invalid Value", "Error. Please enter a valid current setpoint value.")
                return False

    def saveCurrentOffset(self, _=None): 
        """
        Save current offset and uses to offset the graph.
        QUESTION: Range for current offset?

        Args:
            event (_type_): [ADD DESCRIPTION HERE.]
        """
        if self.check_connection():
            self.root.focus()
            return
        else:
            try:
                self.curr_offset = float(self.label4.get())
                #print(f"\nSaved current offset value: {self.curr_offset} nA")
                self.root.focus()
            except ValueError:
                self.root.focus()
                self.label4.delete(0,END)
                self.label4.insert(0,0.000)
                messagebox.showerror("Invalid Value", "Error. Please enter a valid input.")

    def saveSampleBias(self, _=None): 
        """
        Function to send vbias msg to the MCU and waits for a DONE response, 
        witha  valid range of -10 V to 10 V.

        Args:
            event (_type_): [ADD DESCRIPTION HERE.]
        """
        global vbias_save
        global vbias_done_flag
        
        
        if self.check_connection():
            self.root.focus()
            return
        
        else:
            self.root.focus()
            port = self.parent.serial_ctrl.serial_port
            try:
                #print("\n----------SENDING SAMPLE BIAS----------")
                
                vbias_save = self.get_float_value(self.label6, 1.0, "Voltage Bias")
                
                if vbias_save < globals.VBIAS_MIN:
                    vbias_save = globals.VBIAS_MIN + 1
                    messagebox.showerror("Invalid Value", f"Invalid input. Sample bias defaulted to {vbias_save}.")
                elif vbias_save > globals.VBIAS_MAX:
                    vbias_save = globals.VBIAS_MAX - 1
                    messagebox.showerror("Invalid Value", f"Invalid input. Sample bias defaulted to {vbias_save}.")
                
                self.label6.delete(0, END)
                self.label6.insert(0, vbias_save)
                    
                # Clear buffer
                self.parent.clear_buffer()
                         
                start_time = time.time()
                success = self.send_msg_retry(port, globals.MSG_A, ztmCMD.CMD_SET_VBIAS.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 0, vbias_save, 0)

                while not success and (time.time() - start_time) < globals.TIMEOUT:
                    success = self.send_msg_retry(port, globals.MSG_A, ztmCMD.CMD_SET_VBIAS.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 0, vbias_save, 0)
                
                if isinstance(success, bool):       # if we received a DONE msg
                    if success:
                        #print(f"Saved sample bias: {vbias_save} V")
                        return
                    else:
                        messagebox.showinfo("Information", "Did not process change in value within timeout period. Please try again.")
                elif isinstance(success, float):    # if we received a MEASUREMENT msg
                    # Clear buffer
                    self.parent.clear_buffer()
                    
                    # Get newest vbias value
                    testMsg = self.parent.serial_ctrl.ztmGetMsg()

                    _, vbias_new, _ = self.parent.ztm_serial.unpackRxMsg(testMsg)
                    
                    if abs(vbias_new - vbias_save) <= 0.05 * vbias_save:
                        #print(f"Saved sample bias: {vbias_save} V")
                        return
                    else:
                        messagebox.showinfo("Information", "Did not process change in value within timeout period. Please try again.")
                        #print("Not received.")
                else:
                    messagebox.showinfo("Information", "Did not process change in value within timeout period. Please try again.")
                    
            except ValueError:
                self.root.focus()
                self.sample_size.delete(0, END)
                messagebox.showerror("Invalid Value", "Please enter a number from -10 to 10.")
            
            
    def saveSampleRate(self, _=None):
        """
        Saves sample rate as an integer and sends that to the MCU.

        Args:
            _ (_type_): [ADD DESCRIPTION HERE.]
        """
        global sample_rate_done_flag
        global sample_rate_save
        if self.check_connection():
            return
        else:
            #print("\n----------SENDING SAMPLE RATE----------")
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
            #print(f"Saved sample rate value: {self.sample_rate_var.get()}")

            # Clear buffer
            self.parent.clear_buffer()
                        
            start_time = time.time()
            success = self.send_msg_retry(port, globals.MSG_B, ztmCMD.CMD_SET_ADC_SAMPLE_RATE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, sample_rate_save)

            while not success and (time.time() - start_time) < globals.TIMEOUT:
                success = self.send_msg_retry(port, globals.MSG_B, ztmCMD.CMD_SET_ADC_SAMPLE_RATE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, sample_rate_save)
            
            if success:
                sample_rate_done_flag = 1
                return
            else:
                sample_rate_done_flag = 0
                messagebox.showinfo("Information", "Did not process change in value within timeout period. Please try again.")
                
    def saveSampleSize(self, _=None):
        """
        Send sample size as an integer and sends that to the MCU with a
        valid range of 1 to 1024.

        Args:
            _ (_type_): [ADD DESCRIPTION HERE.]
        """
        global sample_size_save
        global sample_size_done_flag
        if self.check_connection():
            self.root.focus()
            return
        else:
            self.root.focus()
            port = self.parent.serial_ctrl.serial_port
            try:
                #print("\n----------SENDING SAMPLE SIZE----------")
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
                
                #print(f"Saved sample size value: {sample_size_save}")

                # Clear buffer
                self.parent.clear_buffer()
                         
                start_time = time.time()
                success = self.send_msg_retry(port, globals.MSG_B, ztmCMD.CMD_SET_ADC_SAMPLE_SIZE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, sample_size_save)

                while not success and (time.time() - start_time) < globals.TIMEOUT:
                    success = self.send_msg_retry(port, globals.MSG_B, ztmCMD.CMD_SET_ADC_SAMPLE_SIZE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, sample_size_save)
                
                if success:
                    sample_size_done_flag = 1
                    return
                else:
                    sample_size_done_flag = 0
                    messagebox.showinfo("Information", "Did not process change in value within timeout period. Please try again.")
                    
            except ValueError:
                self.root.focus()
                self.sample_size.delete(0, END)
                messagebox.showerror("Invalid Value", "Please enter a whole number from 1 to 1024.")
                        
    def saveStepperMotorAdjust(self, _=None):
        """
        Saves adjust stepper motor step size as an integer 'fine_adjust_step_size' .

        Args:
            _ (_type_): [ADD DESCRIPTION HERE.]
        """
        if self.check_connection():
            return
        else:
            if self.coarse_adjust_var.get() == "Full":
                self.fine_adjust_step_size = globals.FULL_STEP
                approx_step_distance = globals.FULL_STEP_DISTANCE   
            elif self.coarse_adjust_var.get() == "Half":
                self.fine_adjust_step_size = globals.HALF_STEP
                approx_step_distance = globals.HALF_STEP_DISTANCE   
            elif self.coarse_adjust_var.get() == "Quarter":
                self.fine_adjust_step_size = globals.QUARTER_STEP
                approx_step_distance = globals.QUARTER_STEP_DISTANCE   
            elif self.coarse_adjust_var.get() == "Eighth":
                self.fine_adjust_step_size = globals.EIGHTH_STEP
                approx_step_distance = globals.EIGHTH_STEP_DISTANCE  
            
            #print("\n---------- SENDING STEPPER MOTOR STEP SIZE ----------")
            # Print confirmation to terminal
            #print(f"\nSaved fine adjust step size: {self.coarse_adjust_var.get()} : {approx_step_distance} nm")

            # Display approx distance per step size to user
            self.label5.configure(text=f"{approx_step_distance:.3f} nm")

    def stepper_motor_up(self):
        """
        Handles the button click for the stepper motor up arrow.
        """
        if self.check_connection():
            return
        else:
            self.step_up = 1
            self.step_down = 0
            self.sendStepperMotorAdjust()
    
    def stepper_motor_down(self):
        """
        Handles the button click for the stepper motor down arrow.
        """
        if self.check_connection():
            return
        else:
            self.step_down = 1
            self.step_up = 0
            self.sendStepperMotorAdjust()

    def sendStepperMotorAdjust(self):
        """
        Send stepper motor adjust msg to the MCU.
        """
        if self.check_connection():
            return
        else:
            port = self.parent.serial_ctrl.serial_port
            
            # fine adjust direction : direction = 0 for up, 1 for down
            if self.step_up:
                fine_adjust_dir = globals.DIR_UP
                self.step_up    = 0 
                dir_name = "UP"
            elif self.step_down:
                fine_adjust_dir = globals.DIR_DOWN
                self.step_down  = 0
                dir_name = "DOWN"
                
            #print(f"\n----------SENDING STEPPER MOTOR {dir_name}----------")
            # Clear buffer
            self.parent.clear_buffer()
                        
            start_time = time.time()
            success = self.send_msg_retry(port, globals.MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, self.fine_adjust_step_size, fine_adjust_dir, globals.NUM_STEPS)

            while not success and (time.time() - start_time) < globals.TIMEOUT:
                success = self.send_msg_retry(port, globals.MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, self.fine_adjust_step_size, fine_adjust_dir, globals.NUM_STEPS)
            
            if success:
                return
            else:
                messagebox.showinfo("Information", "Did not process change in value within timeout period. Please try again.")
              
    def save_home(self):
        """
        Function to save the new home position, where the tip is at when the function is called.
        """
        global curr_pos_total_steps
        global home_pos_total_steps
        if self.check_connection():
            return
        else:
            #print("\n----------SETTING NEW HOME POSITION----------")
            port = self.parent.serial_ctrl.serial_port
            
            # Clear buffer
            self.parent.clear_buffer()
            
            start_time = time.time()
            curr_pos_total_steps = self.send_msg_retry(port, globals.MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_STEP_COUNT.value)

            while not curr_pos_total_steps and (time.time() - start_time) < globals.TIMEOUT:
                curr_pos_total_steps = self.send_msg_retry(port, globals.MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_STEP_COUNT.value)
            
            if curr_pos_total_steps:
                home_pos_total_steps = curr_pos_total_steps
                #print(f"Saved home position (in number of steps): {home_pos_total_steps}")
                return
            else:
                messagebox.showinfo("Information", "Did not process change in value within timeout period. Please try again.")

    def return_home(self):
        """
        Function to return to the home position and send it to the MCU.
        """
        global home_pos_total_steps
        global curr_pos_total_steps
        if self.check_connection():
            return
        else:
            #print("\n----------RETURN TO HOME POSITION----------")
            # Request total step for stepper motor from MCU
            port = self.parent.serial_ctrl.serial_port
            
            # Clear buffer
            self.parent.clear_buffer()
            
            start_time = time.time()
            curr_pos_total_steps = self.send_msg_retry(port, globals.MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_STEP_COUNT.value)

            while not curr_pos_total_steps and (time.time() - start_time) < globals.TIMEOUT:
                curr_pos_total_steps = self.send_msg_retry(port, globals.MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_STEP_COUNT.value)
                
            # If a home position has not been set, error message and return from function
            if home_pos_total_steps == None:
                messagebox.showerror("INVALID", f"No home position has been set.")
                return
            elif home_pos_total_steps == curr_pos_total_steps:
                messagebox.showerror("INVALID", f"Stepper motor is already at home position.")
                return
            
            if curr_pos_total_steps:
                
                # If home position is lower than the tip's current position
                if home_pos_total_steps > curr_pos_total_steps:
                    return_dir = 1 # down
                    num_of_steps = (home_pos_total_steps - curr_pos_total_steps) * 8
                    #print(f"Home position is lower than the current position by: {num_of_steps} (# of 1/8 steps)")

                    # Send command to stepper motor for number of steps between current position and home position
                    num_of_steps_int = int(num_of_steps)
                    success = self.send_msg_retry(self.parent.serial_ctrl.serial_port, globals.MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, globals.EIGHTH_STEP, return_dir, num_of_steps_int)
                    #if success:
                        #print("Done returning to home position.")
                    #else:
                        #print("Failed to return to home position.")

                # If home position is higher than the tip's current position
                elif home_pos_total_steps < curr_pos_total_steps:
                    return_dir = 0 # up
                    num_of_steps = (curr_pos_total_steps - home_pos_total_steps) * 8
                    #print(f"Home position is higher than the current position by: {num_of_steps} (# of 1/8) steps")

                    num_of_steps_int = int(num_of_steps)
                    # Send command to stepper motor for number of steps between current position and home position
                    success = self.send_msg_retry(self.parent.serial_ctrl.serial_port, globals.MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, globals.EIGHTH_STEP, return_dir, num_of_steps_int)
                    #if success:
                        #print("Done returning to home position.")
                    #else:
                        #print("Failed to return to home position.")
                curr_pos_total_steps = self.send_msg_retry(self.parent.serial_ctrl.serial_port, globals.MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_STEP_COUNT.value)
            else:
                messagebox.showinfo("Information", "Did not process change in value within timeout period. Please try again.")
                #print("Failed to receive a response from MCU.")

    
    def check_connection(self):
        """
        Function to check that there is a valid port connection.

        Returns:
            boolean: [ADD DESCRIPTION HERE.]
        """
        global startup_flag
        port = self.parent.serial_ctrl.serial_port
        if port is None or startup_flag == 0:
            InfoMsg = f"ERROR. Connect to COM PORT."
            messagebox.showerror("Connection Error", InfoMsg)
            return True
        else:
            return False

    def update_label(self):
        """
        Method to update the value of ADC current in label 2.
        """
        global curr_data
        global vpiezo_dist
        
        # Get current offset from label 4
        try:
            self.curr_offset = float(self.label4.get())
        except ValueError:
            self.curr_offset = 0.0  # Default to 0 if the value is not a valid float
        curr_data += self.curr_offset
        self.label2.configure(text=f"{curr_data:.4f} nA")
        self.label11.configure(text=f"{vpiezo_dist:.4f}")

    '''
    def get_current_label2(self):
        """
        Used to get the current data from widget label 2.

        Returns:
            current_value (float): Float value of the ADC current.
        """
        current_value = float(self.label2.cget("text").split()[0])  # assuming label2 text value is "value" nA
        return current_value
    '''
    
    def save_notes(self, _=None):
        """_summary_

        Args:
            _ (_type_, optional): [ADD DESCRIPTION HERE.] Defaults to None.

        Returns:
            _type_: _description_
        """
        if self.check_connection():
            self.root.focus()
            return
        else:
            self.root.focus()
            note = self.label7.get(1.0, ctk.END)
            note = note.strip()
            return note
    
    def save_date(self, _=None):
        """_summary_

        Args:
            _ (_type_, optional): [ADD DESCRIPTION HERE.] Defaults to None.

        Returns:
            _type_: _description_
        """
        if self.check_connection():
            self.root.focus()
            return
        else:
            self.root.focus()
            date = self.label8.get()
            return date
    
    def DropDownMenu(self):
        """
        Method to list all the File menu options in a drop menu.
        """
        # Create menu bar
        self.menubar = tk.Menu(self.root)
        
        # Create drop-down menu
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Save", command=self.save_graph)
        self.filemenu.add_command(label="Save As", command=self.save_graph_as)
        self.filemenu.add_command(label="Export (.csv)", command=self.export_data)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        
        self.root.config(menu=self.menubar)
    
    def save_graph(self):
        """
        Saves the current graph image with a default file name.
        """
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        default_filename = os.path.join(downloads_folder, "current_graph.png")
        self.parent.graph_gui.fig.savefig(default_filename)
        messagebox.showinfo("Save Graph", f"Graph saved in Downloads as {default_filename}")

    def save_graph_as(self):
        """
        Saves the current graph image with a user-specified file name.
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if file_path:
            self.parent.graph_gui.fig.savefig(file_path)
            messagebox.showinfo("Save Graph As", f"Graph saved as {file_path}")
    
    def export_data(self):
        """
        [ADD DESCRIPTION HERE.]
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w', newline='') as file:
                # collects the user input text from the notes widget
                header_text = self.save_notes()
                header_date = self.save_date()

                # conjoining and formatting data
                headers = ["Time", "Tunneling Current (nA)"]
                data_to_export = [headers]
                data_to_export.extend(zip(self.parent.graph_gui.time_data, self.parent.graph_gui.y_data))

                # writing to file being created
                writer = csv.writer(file)
                # if the header notes widget has been used, include information in .csv
                if header_date:
                    writer.writerow(['Date:', header_date])
                if header_text:
                    writer.writerow(['Notes:',header_text])
                writer.writerows(data_to_export)

            messagebox.showinfo("Export Data", f"Data exported as {file_path}")

###################################################################################################################
#                                                 GraphGUI CLASS                                                  #
###################################################################################################################
class GraphGUI:
    """
    Function to initialize the data arrays and the graphical display.
    """
    def __init__(self, root, meas_gui):
        """
        [ADD DESCRIPTION HERE.]

        Args:
            root (_type_): _description_
            meas_gui (_type_): _description_
        """
        self.root = root
        self.meas_gui = meas_gui

        #configures plot
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Current (nA)')
       
        # initializes graphical data
        self.y_data = []
        self.x_data = []
        # use this to export data with milliseconds included
        self.time_data = []
        self.line, = self.ax.plot([], [], 'r-')

        # Create a canvas to embed the figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=0, column=3, columnspan=6, rowspan=10, padx=10, pady=5)
        
    
    def update_graph(self):
        """
        This will update the visual graph with the data points obtained during
        the Piezo Voltage Sweep. The data points are appended to the data arrays.
        *Updates every 36ms
        """
        global curr_data

        # Fetch current data from label 2
        #current_data = self.meas_gui.get_current_label2()
        #current_data = curr_data
        
        # update data with next data points
        self.y_data.append(curr_data)
        time_now = datetime.datetime.now()
        # append current time to x axis on graph
        self.x_data.append(time_now)
        
        # append time to include milliseconds for exported data
        formatted_time = time_now.strftime('%H:%M:%S.%f')[:-3]
        self.time_data.append(formatted_time)
        
        # update graph with new data
        #self.line.set_data(self.x_data, self.y_data)
        #self.ax.relim()

        # set x-axis parameters
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.xaxis.set_major_locator(mdates.SecondLocator(interval=2))
        # controls how much time is shown within the graph, currently displays the most recent 10 seconds
        self.ax.set_xlim(datetime.datetime.now() - datetime.timedelta(seconds=globals.ROLLOVER_GRAPH_TIME), datetime.datetime.now())
        #self.ax.autoscale_view()
        
        # redraw canvas
        #self.canvas.draw()
        #self.canvas.flush_events()
        
        if len(self.y_data) % 100 == 0:  # Update every 100 data points
            self.line.set_data(self.x_data, self.y_data)
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()
            self.canvas.flush_events()

        
    def reset_graph(self):
        """
        Resets the visual graph and clears the data points.
        """
        self.ax.clear()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Tunneling Current (nA)')
        self.y_data = []
        self.x_data = []
        self.time_data = []
        self.line, = self.ax.plot([], [], 'r-')
        self.canvas.draw()
        self.canvas.flush_events()


if __name__ == "__main__":
    root_gui = RootGUI()
    root_gui.root.mainloop()