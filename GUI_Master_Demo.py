from tkinter import Label, LabelFrame, Button, StringVar, OptionMenu, END
from tkinter import messagebox 
from tkinter import filedialog
import customtkinter as ctk
import serial.tools.list_ports
import tkinter as tk
import serial
import os
import struct
import time
import csv
import datetime
import threading
import math
import matplotlib.dates as mdates
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Import python files
import globals
from IV_Window import IVWindow 
from IZ_Window import IZWindow  
from value_conversion import Convert
from ztmSerialCommLibrary import usbMsgFunctions, ztmCMD, ztmSTATUS
from SPI_Data_Ctrl import SerialCtrl
from GUI_Widgets import HomepageWidgets

###########################################
############# GLOBAL VARIABLES ############
curr_setpoint   = 0.0

# For MCU sent measurements
curr_data       = 0.0
vb_V            = 0.0
vp_V            = 0.0

vpiezo_dist     = 0

vbias_save      = None
vbias_done_flag = 0

# Used for the tip approach
vpiezo_tip      = 0.0
tunneling_steps = 0

# Used for the sample rate
sample_rate_save        = None
sample_rate_done_flag   = 0

# Used for the sample size
sample_size_save        = None
sample_size_done_flag   = 0

# Used for moving the stepper motor
home_pos_total_steps    = None
curr_pos_total_steps    = None

# Used for the tunneling approach
tip_app_total_steps     = None

startup_flag    = 0

TUNN_APPR_FLAG  = 0
CAP_APPR_FLAG   = 0
PERIODICS_FLAG  = 0
STOP_BTN_FLAG   = 0
###########################################


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
        self.root.geometry("1100x650")
        
        # Add a method to quit the application
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
        
        # Initialize serial control
        self.serial_ctrl = SerialCtrl(None, globals.BAUDRATE)
        self.ztm_serial = usbMsgFunctions(self)
					
        # Initialize other components
        self.meas_gui = MeasGUI(self.root, self)
        self.graph_gui = GraphGUI(self.root, self.meas_gui)
        self.com_gui = ComGUI(self.root, self)
        
        # Initialize MeasGUI components
        self.widget_initializer = HomepageWidgets(self.root, self)
        self.widget_initializer.initialize_widgets(self.meas_gui)
        
    def quit_application(self):
        """
        Quits the application and closes the serial read thread.
        """
        if self.serial_ctrl:
            self.serial_ctrl.stop()
        self.root.quit()
    
    def start_reading(self):
        """
        Opens the serial read thread and enables the start of periodic data reading.
        """
        if self.serial_ctrl:
            if(TUNN_APPR_FLAG):
                self.meas_gui.tunneling_approach()
            elif(CAP_APPR_FLAG):
                self.meas_gui.cap_approach()
            elif(PERIODICS_FLAG):
                self.meas_gui.enable_periodics()
            self.serial_ctrl.running = True
    
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
                self.widget_initializer.enable_widgets(self.meas_gui)
                self.meas_gui.stop_leds()
        # Run the stop reading task in a separate thread
        stop_thread = threading.Thread(target=stop_reading_task)
        stop_thread.start()
    
    def clear_buffer(self):
        """
        Clears the serial buffer to make room for other messages.
        """
        if self.serial_ctrl.serial_port.in_waiting > 0:
            self.serial_ctrl.serial_port.read(self.serial_ctrl.serial_port.in_waiting)

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
        self.frame.grid(row=0, column=0, rowspan=3, columnspan=3, padx=5, pady=5, sticky="n")
        self.label_com.grid(column=1, row=0)
        self.drop_com.grid(column=2, row=0, padx=self.padx)
        self.btn_refresh.grid(column=3, row=0, padx=self.padx)
        self.btn_connect.grid(column=3, row=1, padx=self.padx)

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
                
                # Attempt to start the threads
                serial_response = self.parent.serial_ctrl.start()

                if serial_response:
                    self.startup_routine()
                else:
                    self.btn_connect["text"] = "Connect"
                    self.btn_refresh["state"] = "active"
                    self.drop_com["state"] = "active"
                    InfoMsg = f"Failed to connect to {self.clicked_com.get()}."
                    messagebox.showerror("Connection Error", InfoMsg)
                    self.parent.serial_ctrl.running = False
            except serial.SerialException as e:
                self.btn_connect["text"] = "Connect"
                self.btn_refresh["state"] = "active"
                self.drop_com["state"] = "active"
                InfoMsg = f"Failed to connect to {self.clicked_com.get()}: {e}"
                messagebox.showerror("Connection Error", InfoMsg)
                self.parent.serial_ctrl.running = False
        else:
            if self.parent.serial_ctrl:
                self.parent.serial_ctrl.stop()
            self.btn_connect["text"] = "Connect"
            self.btn_refresh["state"] = "active"
            self.drop_com["state"] = "active"
            InfoMsg = f"UART connection using {self.clicked_com.get()} is now closed."
            messagebox.showwarning("Disconnected", InfoMsg)
            
            startup_flag = 0

    def startup_routine(self):
        """
        A message sent to the MCU upon valid connection of a port, starting the MCU program.
        """
        global startup_flag
        
        port = self.parent.serial_ctrl.serial_port
        
        msg_response = self.parent.meas_gui.send_msg_retry(port, globals.MSG_C, ztmCMD.CMD_CLR.value, ztmSTATUS.STATUS_RDY.value, ztmSTATUS.STATUS_ACK.value)   
        
        if msg_response:
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

        # Initialize MeasGUI widgets
        self.initializer = HomepageWidgets(root, parent)
        self.initializer.initialize_widgets(self)
        self.initializer.publish(self)
        
        self.DropDownMenu()
        
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
        
        # Initialize measurement widgets
        self.update_label()

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
        self.start_led_btn.grid(row=0, column=1, sticky="")
    
    def stop_leds(self):
        """
        Method to change the LEDs upon the user pressing the stop button.
        """
        self.stop_led_btn.grid()
        self.start_led_btn.grid_remove()

    def start_tip_appr(self):
        """
        Enables the tunneling approach through its global flag.
        """
        global TUNN_APPR_FLAG
        global CAP_APPR_FLAG
        global PERIODICS_FLAG

        TUNN_APPR_FLAG = 1
        CAP_APPR_FLAG = 0
        PERIODICS_FLAG = 0

        self.start_reading()

    def start_cap_appr(self):
        """
        Enables the capacitance approach through its global flag.
        """
        global TUNN_APPR_FLAG
        global CAP_APPR_FLAG
        global PERIODICS_FLAG

        TUNN_APPR_FLAG = 0
        CAP_APPR_FLAG = 1
        PERIODICS_FLAG = 0
        
        self.start_reading()

    def start_periodics(self):
        """
        Enables the periodic data through its global flag.
        """
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
            STOP_BTN_FLAG = 0
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
        global CAP_APPR_FLAG
        
        if self.check_connection():
            return
        else:
            STOP_BTN_FLAG = 1
            self.parent.stop_reading()
    
    def send_msg_retry(self, port, msg_type, cmd, status, status_response, *params, max_attempts=globals.MAX_ATTEMPTS):
        """
        Function to send a message to the MCU and retry if we do
        not receive expected response.

        Args:
            port (Serial): Port the serial is communicating with.
            msg_type (byte): Send message type byte.
            cmd (byte): Sent command byte.
            status (byte): Sent status byte.
            status_response (byte): Expected status response byte.
            max_attempts (int, optional): Number of maximum attempts that the message will be sent. Defaults to 10.
        Returns:
            float: Depending on the status response, the function will return a specific value or values.
        """
        global curr_data
        global vb_V
        global vp_V
        global vpiezo_tip
        
        attempt = 0

        while attempt < max_attempts:
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
                testMsg = self.parent.serial_ctrl.receive_serial()
                # Unpack data and display on the GUI
                if testMsg:
                    testMsg_hex = [b for b in testMsg]
                    # checks if status byte read is the same as status byte expected AND that the response is 11 bytes long
                    if testMsg_hex[globals.STAT_BYTE] == status_response and len(testMsg) == globals.MSG_BYTES:
                        unpackResponse = self.parent.ztm_serial.unpackRxMsg(testMsg)
                        
                        if isinstance(unpackResponse, tuple):
                            if len(unpackResponse) == 3:
                                if testMsg_hex[globals.STAT_BYTE] == ztmSTATUS.STATUS_MEASUREMENTS.value:
                                    curr_data, vb_V, vp_V = unpackResponse
                                    vpiezo_tip = vp_V
                                    return True
                        else:
                            if testMsg_hex[globals.STAT_BYTE] == ztmSTATUS.STATUS_STEP_COUNT.value:
                                return unpackResponse  
                        return True
                    
                    elif testMsg_hex[globals.STAT_BYTE] == ztmSTATUS.STATUS_NACK.value:
                        return
                    elif testMsg_hex[globals.STAT_BYTE] == ztmSTATUS.STATUS_FAIL.value:
                        return
                    elif testMsg_hex[globals.STAT_BYTE] == ztmSTATUS.STATUS_RESEND.value:
                        return
                    # overcurrent(?)
                    elif testMsg_hex[globals.STAT_BYTE] == ztmSTATUS.STATUS_BUSY.value:
                        return
                    elif testMsg_hex[globals.STAT_BYTE] == ztmSTATUS.STATUS_ERROR.value:
                        return 
                    else:
                        if testMsg_hex[globals.STAT_BYTE] == ztmSTATUS.STATUS_MEASUREMENTS.value:
                            if cmd == ztmCMD.CMD_SET_VBIAS.value:
                                vb_V = round(Convert.get_Vbias_float(struct.unpack('H',bytes(testMsg[7:9]))[0]), 3)
                                return vb_V
                            elif cmd == ztmCMD.CMD_PIEZO_ADJ.value:
                                vp_V = round(Convert.get_Vpiezo_float(struct.unpack('H',bytes(testMsg[9:11]))[0]), 3) 
                                return vp_V
                attempt += 1
                
            else:
                return False
    
    def sendMsgCapApproach(self, port, cmd, status, status_response, max_attempts=globals.MAX_ATTEMPTS, timeout=globals.TIMEOUT):
        """
        Function to send a message to the MCU and retry if we do
        not receive the expected response, using a timeout instead of a fixed sleep.

        Args:
            port (Serial): Port the serial is communicating with.
            cmd (byte): Sent command byte.
            status (byte): Sent status byte.
            status_response (byte): Expected status response byte.
            max_attempts (int): Number of maximum attempts to send the message.
            timeout (float): Timeout period for each attempt in seconds.

        Returns:
            fft_amp, fft_freq (float): FFT amplitude and FFT frequency.
        """
        global curr_data
        global vb_V
        global vp_V
        global vpiezo_tip
        
        attempt = 0
        
        while attempt < max_attempts:
            msg_response = self.parent.ztm_serial.sendMsgC(port, cmd, status)
            
            if msg_response:
                start_time = time.time()
                while (time.time() - start_time) < timeout:
                    # Check if data is available in the serial buffer
                    if self.parent.serial_ctrl.serial_port.in_waiting == globals.MSG_BYTES:
                        testMsg = self.parent.serial_ctrl.ztmGetMsg()
                        if testMsg:
                            testMsg_hex = [b for b in testMsg]
                            
                            if testMsg_hex[globals.STAT_BYTE] == status_response and len(testMsg) == globals.MSG_BYTES:
                                unpackResponse = self.parent.ztm_serial.unpackRxMsg(testMsg)

                                if isinstance(unpackResponse, tuple):
                                    if len(unpackResponse) == 2 and testMsg_hex[globals.STAT_BYTE] == ztmSTATUS.STATUS_FFT_DATA.value:
                                        fft_amp, fft_freq = unpackResponse
                                        curr_data = fft_amp
                                        
                                        return fft_amp, fft_freq
                attempt += 1
            else:
                messagebox.showerror("ERROR", "Error, no response received. Please try again.")
                return False
        messagebox.showerror("ERROR", "Error. Please try again.")
        return False
    
    def get_float_value(self, label, default_value, value_name):
        """
        Method to error check user inputs and update widget.

        Args:
            label (tkinter Label): Label widget.
            default_value (float): Default value the widget could be set to.
            value_name (string): Name of value.

        Returns:
            value (float): Value the widget will be set to.
        """
        try:
            value = float(label.get())
        except ValueError:
            messagebox.showerror("INVALID VALUE", f"Invalid input for {value_name}. Using default value of {default_value}.")
            value = default_value
        return value  
    
############################################# TIP APPROACH #################################################
    def tunneling_approach(self):
        """
        This function looks for a desired tunneling current using the traditional algorithm.
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
                # Resets visual graph and data
                self.parent.graph_gui.reset_graph()
                
                # Turns interactive graph on
                plt.ion()
                
                self.startup_leds()
                self.initializer.disable_widgets(self)
                
                while True:
                    if STOP_BTN_FLAG == 1:
                        plt.ioff()
                        break
                    
                    success = self.send_msg_retry(port, globals.MSG_C, ztmCMD.CMD_REQ_DATA.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_MEASUREMENTS.value)
                    
                    if success:
                        # Immediately step back and return if current >= target
                        if(curr_data >= curr_setpoint):
                            adjust_success = self.send_msg_retry(port, globals.MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, globals.EIGHTH_STEP, globals.DIR_DOWN, globals.NUM_STEPS)
                            if adjust_success:
                                tunneling_steps -= globals.INC_EIGHT
                                plt.ioff()
                                #return 1, curr_data, vb_V, vp_V, tunneling_steps
                            else:
                                messagebox.showerror("ERROR", "Error. Unable to adjust the stepper motor.")
                        else:
                            vpiezo_tip, tunneling_steps = self.auto_move_tip(tunneling_steps, globals.APPROACH_STEP_SIZE_NM, globals.DIR_DOWN)

                        self.update_label()
                        self.parent.graph_gui.update_graph()
                STOP_BTN_FLAG = 0
            else:
                messagebox.showerror("ERROR", "Error. Did not receive correct response back.")
        # Turns interactive graph off
        plt.ioff()
            
    
    def auto_move_tip(self, steps, dist, dir):
        """
        This function changes the tip height using either the piezo or stepper motor.
        Note: If the distance is out of range for the piezo then the stepper motor will step up
        or down, and the new distance will not be exactly what was desired. This function was 
        created for the tunneling_approach function

        Args:
            steps (float): Tne number of steps the microscope moves during the approach.
            dist (float): The desired change in distance in nm.
            dir (int): Direction for tip to move. Send "DOWN" to move tip down and "UP" to move tip up.
        Returns:
            vpiezo_tip (float): Global variable that collects the vpiezo value during the tunneling approach process.
            steps (float): The number of steps the microscope moves during the approach.
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
        #print(f"\nNew vpiezo for tip approach: {vpiezo_tip} V\nStep Count: {steps}")   # Debug 
        return vpiezo_tip, steps
                
    def piezo_full_extend(self):
        """
        This function adjusts the tip down in increments instead of one total distance.

        Args:
            vpiezo_tip (float): Global variable that collects the vpiezo value during the tunneling approach process.
        """
        global vpiezo_tip

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
        This function adjusts the tip up in increments instead of one total distance.

        Returns:
            vpiezo_tip (float): Global variable that collects the vpiezo value during the tunneling approach process.
        """
        global vpiezo_tip

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
        Starts the capacitance approach algorithm in a separate thread to avoid
        freezing the GUI.
        """
        self.cap_approach_thread = threading.Thread(target=self._cap_approach_impl)
        self.cap_approach_thread.start()

    def _cap_approach_impl(self):
        """
        This function gets the tip close to the sample by using the displacement current
        between the tip and the sample. It looks at the difference between the present displacement
        current and a previous displacement current. It uses a circular buffer to store the delayed
        displacement currents.
        """
        global STOP_BTN_FLAG
        
        if self.check_connection():
            return
        else:
            port = self.parent.serial_ctrl.serial_port
            
            # Start Sinusoidal Vbias
            success = self.send_msg_retry(port, globals.MSG_E, ztmCMD.CMD_VBIAS_SET_SINE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, globals.CAP_APPROACH_AMPL, globals.CAP_APPROACH_FREQ)
            
            if success:
                self.parent.graph_gui.reset_graph()
                plt.ion()
                self.startup_leds()
                self.initializer.disable_widgets(self)
                
                fft_meas = self.get_fft_peak()
                if fft_meas is None:
                    return

                # Using deque for efficient circular buffer management
                delay_line = deque([fft_meas] * (globals.DELAY_LINE_LEN + 1), maxlen=globals.DELAY_LINE_LEN + 1)
                peaks = deque([0] * globals.FFT_AVG_LENGTH, maxlen=globals.FFT_AVG_LENGTH)
                
                not_done = True
                fft_count = 0
                detector_count = 0
                
                while not_done:
                    if STOP_BTN_FLAG == 1:
                        plt.ioff()
                        break
                    
                    # Measure fft peak and update the peaks buffer
                    fft_peak = self.get_fft_peak()
                    if fft_peak is None:
                        continue  # Skip this iteration if FFT measurement failed

                    peaks.append(fft_peak)

                    if fft_count >= globals.FFT_AVG_LENGTH - 1:
                        # Calculate the average of the peak measurements
                        fft_meas = self.get_avg_meas(peaks)

                        # Update the circular buffer with the new measurement
                        old_fft_meas = delay_line[0]
                        delay_line.append(fft_meas)

                        # Calculate difference and check if it exceeds the threshold
                        diff = fft_meas - old_fft_meas
                        if diff > globals.CRIT_CAP_SLOPE:
                            detector_count += 1
                            if detector_count >= 3:
                                not_done = False
                        else:
                            detector_count = 0
                            self.send_msg_retry(port, globals.MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, globals.EIGHTH_STEP, globals.DIR_DOWN, globals.CAP_APPROACH_NUM_STEPS)

                        self.update_label()
                        self.parent.graph_gui.update_graph()
                    else:
                        fft_count += 1
                
                STOP_BTN_FLAG = 0    
                plt.ioff()
                self.stop_leds()
                self.initializer.enable_widgets(self)
                self.parent.clear_buffer()
                self.send_msg_retry(port, globals.MSG_C, ztmCMD.CMD_VBIAS_STOP_SINE.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value)
    
    def get_fft_peak(self):
        """
        Retrieve the FFT peak data from the device.

        Returns:
            peak (float): FFT peak data measurement.
        """
        port = self.parent.serial_ctrl.serial_port
        
        result = self.sendMsgCapApproach(port, globals.MSG_C, ztmCMD.CMD_REQ_FFT_DATA.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_FFT_DATA.value)
        if result is None:
            return None
        else:
            peak, _ = result
            return peak
    
    def get_avg_meas(self, measurements):
        """
        Calculate the average of the valid FFT measurements.

        Args:
            measurements (list): List of valid FFT measurements.
        Returns:
            sum(valid_measurements) / len(valid_measurements) (float): Average of the FFT measurements.
        """
        valid_measurements = [m for m in measurements if m is not None]
        if not valid_measurements:
            return None
        return sum(valid_measurements) / len(valid_measurements)
    

    '''
    # OLD METHOD
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
        
        if self.check_connection():
            return
        else:
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
                self.initializer.disable_widgets(self)
                
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
                self.initializer.enable_widgets(self)
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
        
        #sum = 0
        #for i in range(len(measurements)): sum += measurements[i]
        #sum /= len(measurements)
        #return sum
    '''
    
    def enable_periodics(self):
        """
        Function to enable and read periodic data from the MCU.
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
                # Resets visual graph and data
                self.parent.graph_gui.reset_graph() 
                # Turns interactive graph on
                plt.ion()
                
                self.startup_leds()
                self.initializer.disable_widgets(self)
                
                while True:
                    if STOP_BTN_FLAG == 1:
                        plt.ioff()
                        break
                    
                    response = self.parent.serial_ctrl.ztmGetMsg()
                    if response:
                        if response[globals.STAT_BYTE] == ztmSTATUS.STATUS_MEASUREMENTS.value or response[globals.STAT_BYTE] == ztmSTATUS.STATUS_ACK.value:
                            curr_data = round(struct.unpack('f', bytes(response[3:7]))[0], 3) 
                    self.update_label()
                    self.parent.graph_gui.update_graph()
                STOP_BTN_FLAG = 0    
            else:
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
            port = self.parent.serial_ctrl.serial_port
            
            delta_v_float = self.get_float_value(self.label10, 1.0, "Piezo Voltage")
            if globals.VPIEZO_MIN <= self.total_voltage <= globals.VPIEZO_MAX:
                if self.vpzo_up:
                    if self.total_voltage + delta_v_float <= globals.VPIEZO_MAX:
                        self.total_voltage += delta_v_float
                    else:
                        self.total_voltage = globals.VPIEZO_MAX
                        messagebox.showerror("INVALID", "Total voltage exceeds 10 V. Maximum allowed is 10 V.")
                        return
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
            if isinstance(success, bool):       # If we received a DONE msg
                if success:
                    self.label12.configure(text=f"{self.total_voltage:.3f} ")
                    return
                else:
                    messagebox.showinfo("Information", "Did not process change in value within timeout period. Please try again.")
            elif isinstance(success, float):    # If we received a MEASUREMENT msg
                # Clear buffer
                self.parent.clear_buffer()
                
                # Get msg
                testMsg = self.parent.serial_ctrl.ztmGetMsg()

                # Unpack new vpzo value
                _, _, vpzo_new = self.parent.ztm_serial.unpackRxMsg(testMsg)
                
                if abs(vpzo_new - self.total_voltage) <= 0.05 * self.total_voltage:
                    self.label12.configure(text=f"{self.total_voltage:.3f} ")
                    return
                else:
                    messagebox.showinfo("Information", f"Did not process change in value within {globals.TIMEOUT} period. Please try again.")
                
    def saveCurrentSetpoint(self, _=None): 
        """
        Function to save the user inputted value of current setpoint to use for 
        the tip approach algorithm. The valid range is 0.1 nA to 10 nA.
        
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
                        return
                    else:
                        messagebox.showinfo("Information", "Did not process change in value within timeout period. Please try again.")
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
            
            # Fine adjust direction : direction = 0 for up, 1 for down
            if self.step_up:
                fine_adjust_dir = globals.DIR_UP
                self.step_up    = 0 
            elif self.step_down:
                fine_adjust_dir = globals.DIR_DOWN
                self.step_down  = 0

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
            port = self.parent.serial_ctrl.serial_port
            
            # Clear buffer
            self.parent.clear_buffer()
            
            start_time = time.time()
            curr_pos_total_steps = self.send_msg_retry(port, globals.MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_STEP_COUNT.value)

            while not curr_pos_total_steps and (time.time() - start_time) < globals.TIMEOUT:
                curr_pos_total_steps = self.send_msg_retry(port, globals.MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_STEP_COUNT.value)
            if curr_pos_total_steps:
                home_pos_total_steps = curr_pos_total_steps
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
                    
                    # Send command to stepper motor for number of steps between current position and home position
                    num_of_steps_int = int(num_of_steps)
                    self.send_msg_retry(self.parent.serial_ctrl.serial_port, globals.MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, globals.EIGHTH_STEP, return_dir, num_of_steps_int)

                # If home position is higher than the tip's current position
                elif home_pos_total_steps < curr_pos_total_steps:
                    return_dir = 0 # up
                    num_of_steps = (curr_pos_total_steps - home_pos_total_steps) * 8
                    num_of_steps_int = int(num_of_steps)
                    # Send command to stepper motor for number of steps between current position and home position
                    self.send_msg_retry(self.parent.serial_ctrl.serial_port, globals.MSG_D, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, globals.EIGHTH_STEP, return_dir, num_of_steps_int)
                curr_pos_total_steps = self.send_msg_retry(self.parent.serial_ctrl.serial_port, globals.MSG_C, ztmCMD.CMD_REQ_STEP_COUNT.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_STEP_COUNT.value)
            else:
                messagebox.showinfo("Information", "Did not process change in value within timeout period. Please try again.")
    
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

    def save_notes(self, _=None):
        """
        Method to save the notes inputted by the user in the notes widget.

        Args:
            _ (_type_, optional): [ADD DESCRIPTION HERE.] Defaults to None.

        Returns:
            note (string): _description_
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
        """
        Method to save the date inputted by the user in the notes widget.

        Args:
            _ (_type_, optional): [ADD DESCRIPTION HERE.] Defaults to None.

        Returns:
            date (string): _description_
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
        Method to list all the file menu options in a drop menu.
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
        Menu option to export graph data into a CSV file.
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w', newline='') as file:
                # Collects the user input text from the notes widget
                header_text = self.save_notes()
                header_date = self.save_date()

                # Conjoining and formatting data
                headers = ["Time", "Tunneling Current (nA)"]
                data_to_export = [headers]
                data_to_export.extend(zip(self.parent.graph_gui.time_data, self.parent.graph_gui.y_data))

                # Writing to file being created
                writer = csv.writer(file)
                # If the header notes widget has been used, include information in .csv
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
        This initializes the graph widget for the three different processes.
        
        Args:
            root (_type_): _description_
            meas_gui (_type_): _description_
        """
        self.root = root
        self.meas_gui = meas_gui

        # Configures plot
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Current (nA)')
       
        # Initializes graphical data
        self.y_data = []
        self.x_data = []
        # Use this to export data with milliseconds included
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
        global sample_size_save
        global PERIODICS_FLAG
        global CAP_APPR_FLAG
        global TUNN_APPR_FLAG
        
        # Local variables - calculate update interval based on sample size
        A = 1900    # Scaling factor
        k = 0.005   # Decay rate
        B = 100     # Minimum interval

        # Update data with next data points
        self.y_data.append(curr_data)
        time_now = datetime.datetime.now()
        # Append current time to x axis on graph
        self.x_data.append(time_now)
        
        # Append time to include milliseconds for exported data
        formatted_time = time_now.strftime('%H:%M:%S.%f')[:-3]
        self.time_data.append(formatted_time)

        # Set x-axis parameters
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.xaxis.set_major_locator(mdates.SecondLocator(interval=2))
        # Controls how much time is shown within the graph, currently displays the most recent 10 seconds
        self.ax.set_xlim(datetime.datetime.now() - datetime.timedelta(seconds=globals.ROLLOVER_GRAPH_TIME), datetime.datetime.now())

        if PERIODICS_FLAG:
            # Sample size can be set by the user, but default is 1024
            if sample_size_save == None:
                if len(self.y_data) % 100 == 0:  # Updates every 100 data points
                    self.line.set_data(self.x_data, self.y_data)
                    self.ax.relim()
                    self.ax.autoscale_view()
                    self.canvas.draw()
                    self.canvas.flush_events()
            else:
                # Calculate update interval using exponential decay
                update_interval = int(A* math.exp(-k * sample_size_save) + B)
                # Ensure interval doesn't fall below minimum value
                update_interval = max(update_interval, B)
                
                if len(self.y_data) % update_interval == 0: 
                    self.line.set_data(self.x_data, self.y_data)
                    self.ax.relim()
                    self.ax.autoscale_view()
                    self.canvas.draw()
                    self.canvas.flush_events()
        
        elif TUNN_APPR_FLAG:
            # Sample size is set to 24
            if len(self.y_data) % 150 == 0: 
                self.line.set_data(self.x_data, self.y_data)
                self.ax.relim()
                self.ax.autoscale_view()
                self.canvas.draw()
                self.canvas.flush_events()
            
        elif CAP_APPR_FLAG:
            # FFT data sets sample size to 1024
            if len(self.y_data) % 10 == 0: 
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