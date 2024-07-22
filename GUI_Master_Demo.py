from tkinter import *
from tkinter import messagebox, filedialog
from PIL import Image, ImageGrab
import customtkinter as ctk
import serial, re, os, struct, time
import serial.tools.list_ports
import re

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from IV_Window import IVWindow  # import the IV Window Class
from IZ_Window import IZWindow  # import the IV Window Class
from SPI_Data_Ctrl import SerialCtrl
from Data_Com_Ctrl import DataCtrl
from value_conversion import Convert
from ztmSerialCommLibrary import ztmCMD, ztmSTATUS, usbMsgFunctions, MSG_A, MSG_B, MSG_C, MSG_D, MSG_E, MSG_F
#from value_conversion import Convert


class RootGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Homepage")
        self.root.config(bg="#eeeeee")
        self.root.geometry("1100x650")
        
        # Add a method to quit the application
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
        
        # initialize data and serial control
        self.data_ctrl = DataCtrl(9600, self.handle_data)
        self.serial_ctrl = SerialCtrl('COM9', 9600, self.data_ctrl.decode_data)
        self.data_ctrl.set_serial_ctrl(self.serial_ctrl)
        self.ztm_serial = usbMsgFunctions(self)
					
        
        # Initialize other components
        self.meas_gui = MeasGUI(self.root, self)
        self.graph_gui = GraphGUI(self.root)
        #self.button_gui = ButtonGUI(self.root, self)
        self.com_gui = ComGUI(self.root, self)
        
    def quit_application(self):
        print("Quitting application")
        if self.serial_ctrl:
            self.serial_ctrl.stop()
        self.root.quit()
    
    def start_reading(self):
        print("Starting to read data...")
        if self.serial_ctrl:
            print("Serial controller is initialized, starting now...")
            self.serial_ctrl.start()
            
            port = self.serial_ctrl.serial_port
            #print(port)
            self.meas_gui.send_parameters(port)
        else:
            print("Serial controller is not initialized.")
    
    def stop_reading(self):
        print("Stopped reading data...")
        self.serial_ctrl.stop()
        
    # ??
    def update_distance(self, adc_curr, vbias, vpzo):
        print(f"RootGUI: Updating distance with data: ADC_CURR={adc_curr}, VBIAS={vbias}, VPZO={vpzo}")
        self.meas_gui.update_distance(adc_curr, vbias, vpzo)
    
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
        if self.clicked_com.get() == "-" and self.sample_rate_var.get == "-":
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
                print(f"Connecting to {port}...")
                self.btn_connect["text"] = "Disconnect"
                self.btn_refresh["state"] = "disable"
                self.drop_com["state"] = "disable"
                InfoMsg = f"Successful UART connection using {self.clicked_com.get()}."
                messagebox.showinfo("Connected", InfoMsg)
                self.parent.serial_ctrl.start()
            except serial.SerialException as e:
                InfoMsg = f"Failed to connect to {port}: {e}"
                messagebox.showerror("Connection Error", InfoMsg)
                print(f"Failed to connect to {port}: {e}")
        else:
            if self.parent.serial_ctrl:
                self.parent.serial_ctrl.stop()
            self.btn_connect["text"] = "Connect"
            self.btn_refresh["state"] = "active"
            self.drop_com["state"] = "active"
            InfoMsg = f"UART connection using {self.clicked_com.get()} is now closed."
            messagebox.showwarning("Disconnected", InfoMsg)
            print("Disconnected")

  
# class for measurements/text box widgets in homepage
class MeasGUI:
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent					
            
        # sample rate adjust
        self.frame8 = LabelFrame(root, text="", padx=5, pady=5, bg="#ADD8E6")
        self.label_sample_rate = Label(self.frame8, text="Sample Rate: ", bg="#ADD8E6", width=11, anchor="w")
        self.sample_rate_var = StringVar()
        self.sample_rate_var.set("-")
        self.sample_rate_menu = OptionMenu(self.frame8, self.sample_rate_var, "25 kHz", "12.5 kHz", "37.5 kHz", "10 kHz", "5 kHz", command=self.saveSampleRate) # command=self.sample_rate_selected) 
        self.sample_rate_menu.config(width=7)

        self.label_sample_rate.grid(column=1, row=1)
        self.sample_rate_menu.grid(column=2, row=1) #, padx=self.padx)
        self.frame8.grid(row=13, column=4, padx=5, pady=5, sticky="")

        # fine adjust step size
        self.frame9 = LabelFrame(root, text="", padx=5, pady=5, bg="#ADD8E6")
        self.label_fine_adjust = Label(self.frame9, text="Step Size: ", bg="#ADD8E6", width=8, anchor="w")
        self.fine_adjust_var = StringVar()
        self.fine_adjust_var.set("-")
        self.fine_adjust_menu = OptionMenu(self.frame9, self.fine_adjust_var, "Full", "Half", "Quarter", "Eighth", command=self.saveFineAdjust) 
        self.fine_adjust_menu.config(width=6)

        self.label_fine_adjust.grid(column=1, row=1)
        self.fine_adjust_menu.grid(column=1, row=2) #, padx=self.padx)
        self.frame9.grid(row=12, column=2, rowspan=2, columnspan=2, padx=5, pady=5, sticky="")
        self.label_fine_adjust_inc = Label(self.frame9, text="Approx. Dist", bg="#ADD8E6", width=9, anchor="w")

        self.label5 = Label(self.frame9, bg="white", width=10)
        self.label_fine_adjust_inc.grid(column=2, row=1)
        self.label5.grid(column=2, row=2, padx=5, pady=5)

        # vpiezo adjust step size
        self.frame10 = LabelFrame(root, text="", padx=5, pady=5, bg="#d0cee2")
        self.label_vpeizo_delta = Label(self.frame10, text="Vpiezo ΔV (V):", bg="#d0cee2", width=11, anchor="w")
        self.label_vpeizo_delta.grid(column=1, row=1)
        self.frame10.grid(row=7, column=2, rowspan=4, columnspan=2, padx=5, pady=5, sticky="")
        self.label_vpeizo_delta_distance = Label(self.frame10, text="Approx. Dist", bg="#d0cee2", width=9, anchor="w")
        self.label_vpeizo_delta_distance.grid(column=2, row=1)
        self.label10 = Entry(self.frame10, bg="white", width=10)
        self.label10.bind("<Return>", self.savePiezoIncrement)
        self.label11 = Label(self.frame10, bg="white", width=10)
        self.label10.grid(column=1, row=2, padx=5)
        self.label11.grid(column=2, row=2, padx=5)
        self.label_vpeizo_total = Label(self.frame10, text="Total Voltage", bg="#d0cee2", width=10, anchor="w")
        self.label_vpeizo_total.grid(column=1, row=3, columnspan=2)
        self.label12 = Label(self.frame10, bg="white", width=10)
        self.label12.grid(column=1, row=4, columnspan=2)

        # distance
        self.frame1 = LabelFrame(root, text="Distance (nm)", padx=10, pady=2, bg="gray", width=20)
        self.label1 = Label(self.frame1, bg="white", width=20)
        
        # current
        self.frame2 = LabelFrame(root, text="Current (nA)", padx=10, pady=2, bg="gray")
        self.label2 = Label(self.frame2, bg="white", width=20)
        
        # current setpoint
        self.frame3 = LabelFrame(root, text="Current Setpoint (nA)", padx=10, pady=2, bg="#ADD8E6")
        self.label3 = Entry(self.frame3, bg="white", width=24)
        self.label3.bind("<Return>", self.saveCurrentSetpoint)
        
        # current offset
        self.frame4 = LabelFrame(root, text="Current Offset (nA)", padx=10, pady=2, bg="#ADD8E6")
        self.label4 = Entry(self.frame4, bg="white", width=24)
        self.label4.bind("<Return>", self.saveCurrentOffset)
         
        # sample bias
        self.frame6 = LabelFrame(root, text="Sample Bias (V)", padx=10, pady=2, bg="#ADD8E6")
        self.label6 = Entry(self.frame6, bg="white", width=24)
        self.label6.bind("<Return>", self.saveSampleBias)

        # user notes text box
        self.frame7 = LabelFrame(root, text="NOTES", padx=10, pady=5, bg="#ADD8E6")
        self.label7 = Text(self.frame7, height=7, width=30)
        self.label8 = Text(self.frame7, height=1, width=8)
        self.label9 = Label(self.frame7, padx=10, text="Date:", height=1, width=5)

        # setup the drop option menu
        self.DropDownMenu()
        
        # optional graphic parameters
        self.padx = 20
        self.pady = 10
        
        # Initialize data attributes for continuous update
        self.distance = 0
        self.adc_curr = 0
        self.vbias = 0
        self.vpzo = 0
        self.update_label()
        
        # put on the grid all the elements
        self.publish()
    
        # define images
        self.add_btn_image0 = ctk.CTkImage(Image.open("Images/Vpzo_Up_Btn.png"), size=(40,40))
        self.add_btn_image1 = ctk.CTkImage(Image.open("Images/Vpzo_Down_Btn.png"), size=(40,40))
        self.add_btn_image2 = ctk.CTkImage(Image.open("Images/Fine_Adjust_Btn_Up.png"), size=(40,40))
        self.add_btn_image3 = ctk.CTkImage(Image.open("Images/Fine_Adjust_Btn_Down.png"), size=(40,40))
        self.add_btn_image4 = ctk.CTkImage(Image.open("Images/Start_Btn.png"), size=(90,35))
        self.add_btn_image5 = ctk.CTkImage(Image.open("Images/Stop_Btn.png"), size=(90,35))
        self.add_btn_image6 = ctk.CTkImage(Image.open("Images/Acquire_IV.png"), size=(90,35))
        self.add_btn_image7 = ctk.CTkImage(Image.open("Images/Acquire_IZ.png"), size=(90,35))
        self.add_btn_image8 = ctk.CTkImage(Image.open("Images/Stop_LED.png"), size=(35,35))
        # self.add_btn_image9 = ctk.CTkImage(Image.open("Images/Start_LED.png"), size=(35,35))
        self.add_btn_image10 = ctk.CTkImage(Image.open("Images/Save_Home_Btn.png"), size=(90,35))
        self.add_btn_image11 = ctk.CTkImage(Image.open("Images/Return_Home_Btn.png"), size=(35,35))
        
        # create buttons with proper sizes															   
        self.start_btn = ctk.CTkButton(master=root, image=self.add_btn_image4, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.start_reading)
        self.stop_btn = ctk.CTkButton(master=root, image=self.add_btn_image5, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.stop_reading)
        self.acquire_iv_btn = ctk.CTkButton(master=root, image=self.add_btn_image6, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.open_iv_window)
        self.acquire_iz_btn = ctk.CTkButton(master=root, image=self.add_btn_image7, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.open_iz_window)
        self.stop_led_btn = ctk.CTkButton(master=root, image=self.add_btn_image8, text="", width=30, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, hover=NONE)
        
        self.save_home_pos = ctk.CTkButton(master=root, image=self.add_btn_image10, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0)
        self.return_to_home_pos = ctk.CTkButton(master=root, image=self.add_btn_image11, text="", width=30, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0)

        self.vpiezo_btn_frame = LabelFrame(root, text="Retract Tip", padx=10, pady=5, bg="#eeeeee")
        self.vpiezo_adjust_btn_up = ctk.CTkButton(master=self.vpiezo_btn_frame, image=self.add_btn_image0, text = "", width=40, height=40, compound="bottom", fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0)
        self.vpiezo_adjust_btn_down = ctk.CTkButton(master=self.vpiezo_btn_frame, image=self.add_btn_image1, text="", width=40, height=40, compound="bottom", fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0)
        
        self.fine_adjust_frame = LabelFrame(root, text="Fine Adjust", padx=10, pady=5, bg="#eeeeee")
        self.fine_adjust_btn_up = ctk.CTkButton(master=self.fine_adjust_frame, image=self.add_btn_image2, text = "", width=40, height=40, compound="bottom", fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.handle_fine_adjust_up)
        self.fine_adjust_btn_down = ctk.CTkButton(master=self.fine_adjust_frame, image=self.add_btn_image3, text="", width=40, height=40, compound="bottom", fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.handle_fine_adjust_down)

        '''
        self.vbias_frame = LabelFrame(root, text="Vbias", padx=10, pady=2, bg="#7393B3")
        self.vbias_label = Entry(self.vbias_frame, bg="white", width=15)
        '''


        self.DisplayGUI()
        
    # def sample_rate_selected(self, _):
    #     if self.sample_rate_var.get() != "-" and self.clicked_com.get() != "-":
    #         self.btn_connect["state"] = "active"
    #     else:
    #         self.btn_connect["state"] = "disabled"

    def DisplayGUI(self):
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
        self.return_to_home_pos.grid(row=9, column=9)

        # positioning for save parameters button
        # self.save_params_button.grid(row=14, column=4, columnspan=2)

    '''
        self.vbias_frame.grid(row=6, column=9, padx=5, pady=5, sticky="ne")
        self.vbias_label.grid(row=6, column=9, padx=5, pady=5)
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
        new_window = ctk.CTkToplevel(self.root)
        IZWindow(new_window)
    
    def start_reading(self):
        print("ButtonGUI: Start button pressed")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.parent.start_reading()

        #port = self.serial_ctrl.port
        #self.send_parameters(port)
							  
    
    def stop_reading(self):
        print("ButtonGUI: Stop button pressed")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.parent.stop_reading()


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
    Function to error check user inputs
    '''
    def get_float_value(self, label, default_value, value_name):
        try:
            value = float(label.get())
            print(value)
        except ValueError:
            print(f"Invalid input for {value_name}. Using default value of {default_value}.")
            value = default_value
        return value  
    
    '''
    Function to send user-inputted parameters to MCU
    sample bias, vpiezo, step size, current setpoint, sample rate
    '''        
    def send_parameters(self, port):

        adc_curr = self.get_float_value(self.label3, 0.0, "ADC Current")
        vbias = self.get_float_value(self.label6, 0.0, "Voltage Bias")
        vpzo = self.get_float_value(self.label10, 0.0, "Vpiezo")
        # number of steps, hardcoded = 1, for fine adjust arrows
        num_of_steps = 1
        # fine adjust direction
        fine_adjust_dir = 0 #self.fine_adjust_direction
        # # sample rate
        # sample_rate = self.sample_rate # integer in kHz
        
        # # NEW FUNCTION
        #### send user fine adjust command and params to mcu
        self.parent.ztm_serial.sendMsgD(port, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_STEP_COUNT.value, self.fine_adjust_step_size, fine_adjust_dir, num_of_steps)
        
        # NEW FUNCTION 
        #### Send user input parameters to the MCU
        self.parent.ztm_serial.sendMsgA(port, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_DONE.value, 0, 0, vpzo)

        # Initialize counter and response buffer 
        ### Read ACK from the MCU
        ack_response = self.parent.serial_ctrl.read_bytes()
        ### Unpack data and display on the GUI
        if ack_response:
            self.parent.ztm_serial.unpackRxMsg(ack_response)
        else:
            print("Failed to receive response from MCU.")
              
        ### Request data from MCU
        self.parent.ztm_serial.sendMsgC(port, ztmCMD.CMD_REQ_DATA.value, ztmSTATUS.STATUS_CLR.value)
        
        ### Read data from MCU
        data_response = self.parent.serial_ctrl.read_bytes()
        
        ### Unpack data
        if data_response:
            self.parent.ztm_serial.unpackRxMsg(data_response)
            
            # Extracting and displaying the payload
            current_nA = round(struct.unpack('>f', ack_response[3:7])[0], 3)
            vb_V = round(Convert.get_Vbias_float(struct.unpack('>H', ack_response[7:9])[0]), 3)
            vp_V = round(Convert.get_Vpiezo_float(struct.unpack('>H', ack_response[9:11])[0]), 3)

            '''
            # Display the values on the GUI
            self.label1.config(text=f"Current: {current_nA} nA")
            self.label2.config(text=f"Vbias: {vb_V} V")
            self.label10.config(text=f"Vpiezo: {vp_V} V")
            '''
            
            print("Received values\n\tCurrent: " + str(current_nA) + " nA")
            print("\tVbias: " + str(vb_V) + " V")
            print("\tVpiezo: " + str(vp_V) + " V\n")
        else:
            print("Failed to receive response from MCU.")
        
        ### Display data on GUI

    

    # save piezo incremental step input by user to send to mcu
    def savePiezoIncrement(self, event):
        vpiezo_increment = self.label10.get()
        print(f"Saved piezo inc value: {vpiezo_increment}")

    # save current setpoint input by user to send to mcu
    def saveCurrentSetpoint(self, event): 
        curr_setpoint = self.label3.get()
        print(f"Saved current setpoint value: {curr_setpoint}")

    # save current offset input by user to send to mcu
    def saveCurrentOffset(self, event): 
        curr_offset = self.label4.get()
        print(f"Saved current offset value: {curr_offset}")

    # save sample bias voltage input by user to send to mcu
    def saveSampleBias(self, event): 
        sample_bias = self.label6.get()
        print(f"Saved sample bias value: {sample_bias}")

    # saves sample rate input as a integer 'sample_rate' to be sent to mcu
    def saveSampleRate(self, _):
        if self.sample_rate_var.get() == "25 kHz":
            self.sample_rate = 25000
        elif self.sample_rate_var.get() == "12.5 kHz":
            self.sample_rate = 12500
        elif self.sample_rate_var.get() == "37.5 kHz":
            self.sample_rate = 37500
        elif self.sample_rate_var.get() == "10 kHz":
            self.sample_rate = 10000
        elif self.sample_rate_var.get() == "5 kHz":
            self.sample_rate = 5000
        print(f"Saved sample rate value: {self.sample_rate}")
        
        port = self.parent.serial_ctrl.serial_port

        '''
        sendMsgB(port, msgCmd, msgStatus, uint16_rateHz):
            - port          = COM port variable assigned using pySerial functions
            - msgCmd        = ztmCMD value - see documentation for valid commands
            - msgStatus     = ztmStatus value - usually STATUS_CLR
            - uint16_rateHz = data rate to assign, units of Hz, max limit 65535
            - Function transmits Msg B, does not return anything. '''
        self.parent.ztm_serial.sendMsgB(port, ztmCMD.CMD_SET_ADC_SAMPLE_RATE.value, ztmSTATUS.STATUS_CLR.value, self.sample_rate)
        print(f"Sending cmd adjust sample rate to mcu for: {self.sample_rate}")

        ### Read ACK from the MCU
        ack_response = self.parent.serial_ctrl.read_bytes()
        ### Unpack data and display on the GUI
        if ack_response:
            self.parent.ztm_serial.unpackRxMsg(ack_response)
        else:
            print("Failed to receive response from MCU.")

    # save fine adjust stepper motor step size as an integer 'fine_adjust_step_size' to be sent to mcu
    def saveFineAdjust(self, _):
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

    # handles button click for fine adjust up arrow
    def handle_fine_adjust_up(self):
        # fine adjust direction : direction = 0 for up, 1 for down
        fine_adjust_dir = 0 
        
        # number of steps, hardcoded = 1, for fine adjust arrows
        num_of_steps = 1

        port = self.parent.serial_ctrl.serial_port
        print(f"port: {port}")

        #### send user fine adjust command and params to mcu
        # need to figure out port access
        '''sendMsgD(port, msgCmd, msgStatus, size, dir, count):
            - port          = COM port variable assigned using pySerial functions
            - msgCmd        = ztmCMD value - see documentation for valid commands
            - msgStatus     = ztmStatus value - usually STATUS_CLR
            - size          = step size - see global constants, ex. FULL_STEP
            - dir           = direction assignment, raise or lower the top plate of microscope
                              ex. DIR_UP (value should be 1 or 0)
            - count         = number of steps at the designated step size
            - Function transmits Msg D, does not return anything. '''
        self.parent.ztm_serial.sendMsgD(port, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, self.fine_adjust_step_size, fine_adjust_dir, num_of_steps)
        print(f"Sending cmd fine_adjust_up to mcu: {self.fine_adjust_step_size}")

        ### Read ACK from the MCU
        done_response = self.parent.serial_ctrl.read_bytes()
        ### Unpack data and display on the GUI
        # looking for STATUS_DONE
        if done_response:
            print(f"Response recieved: {done_response}")
            status_received = self.parent.ztm_serial.unpackRxMsg(done_response)
            if status_received != ztmSTATUS.STATUS_DONE.value:
                print(f"ERROR: wrong status recieved, status value: {status_received}")
        else:
            print("Failed to receive response from MCU.")
        
    # handles button click for fine adjust down arrow
    def handle_fine_adjust_down(self):
        # fine adjust direction : direction = 0 for up, 1 for down
        fine_adjust_dir = 1 
        
        # number of steps, hardcoded = 1, for fine adjust arrows
        num_of_steps = 1

        port = self.parent.serial_ctrl.serial_port

        #### send user fine adjust command and params to mcu
        # need to figure out port access
        '''sendMsgD(port, msgCmd, msgStatus, size, dir, count):
            - port          = COM port variable assigned using pySerial functions
            - msgCmd        = ztmCMD value - see documentation for valid commands
            - msgStatus     = ztmStatus value - usually STATUS_CLR
            - size          = step size - see global constants, ex. FULL_STEP
            - dir           = direction assignment, raise or lower the top plate of microscope
                              ex. DIR_UP (value should be 1 or 0)
            - count         = number of steps at the designated step size
            - Function transmits Msg D, does not return anything. '''
        self.parent.ztm_serial.sendMsgD(port, ztmCMD.CMD_STEPPER_ADJ.value, ztmSTATUS.STATUS_CLR.value, self.fine_adjust_step_size, fine_adjust_dir, num_of_steps)
        print(f"Sending cmd fine_adjust_down to mcu: {self.fine_adjust_step_size}")

        ### Read ACK from the MCU 
        done_response = self.parent.serial_ctrl.read_bytes()
        ### Unpack data and display on the GUI
        # looking for STATUS_DONE
        if done_response:
            print(f"Response recieved: {done_response}")
            status_received = self.parent.ztm_serial.unpackRxMsg(done_response)
            if status_received != ztmSTATUS.STATUS_DONE.value:
                print(f"ERROR: wrong status recieved, status value: {status_received}")
        else:
            print("Failed to receive response from MCU.")

    # to remove 
    def updateParams(self):
        curr_setpoint = self.label3.get()
        curr_offset = self.label4.get()
        #fine_adjust_inc = self.label5.get()
        Sample_bias = self.label6.get()

        if self.validate_setpoint(curr_setpoint):
            print(f"Entered setpoint: {curr_setpoint}")
        else:
            messagebox.showerror("Error", "Please enter a valid current setpoint")
        
        if self.validate_offset(curr_offset):
            print(f"Entered offset: {curr_offset}")
        else:
            messagebox.showerror("Error", "Please enter a valid current offset")
        
        # if self.validate_fine_adjust_inc(fine_adjust_inc):
        #     print(f"Entered fine adjust inc: {fine_adjust_inc}")
        # else:
        #     messagebox.showerror("Error", "Please enter a valid fine adjust inc")
        
        if self.validate_sample_bias(Sample_bias):
            print(f"Entered sample bias: {Sample_bias}")
        else:
            messagebox.showerror("Error", "Please enter a valid sample bias")
        

    '''
    need to accuractely define the input validations
    '''
    def validate_setpoint(self, setpoint):
        pattern1 = [0-9]
        return re.match(pattern1,setpoint)
    
    def validate_offset(offset):
        pattern2 = [0-9]
        return re.match(pattern2,offset)
    
    # stepper motor or piezo act
    def validate_fine_adjust_inc(fine_inc):
        pattern3 = [0-9]
        return re.match(pattern3,fine_inc)
    
    # -10V to 10V
    def validate_sample_bias(bias):
        pattern4 = [0-9]
        return re.match(pattern4,bias)

    # should be displaying distance and current that is sent from mcu
    def update_distance(self, adc_curr, vbias, vpzo):
        print(f"MeasGUI: Updating distance with data: ADC_CURR={adc_curr}, VBIAS={vbias}, VPZO={vpzo}")
        self.adc_curr = adc_curr
        self.vbias = vbias
        self.vpzo = vpzo
        self.update_label()

    def update_label(self):
        self.label1.configure(text=f"{self.distance:.3f} nm")
        self.label2.configure(text=f"{self.adc_curr:.3f} nA")
        #self.label2.delete(0, END)
        #self.label2.insert(0, f"{self.vbias:.3f}")
        #self.label3.delete(0, END)
        #self.label3.insert(0, f"{self.vpzo:.3f}")
        self.distance = self.distance + 1
        self.adc_curr = self.adc_curr + 1.5
        self.label2.after(1000, self.update_label)
                 
    # file drop-down menu
    def DropDownMenu(self):
        '''
        Method to list all the File menu options in a drop menu
        '''
        self.menu_options = StringVar()
        options = ["File",
                   "Save",
                   "Save As",
                   "Export (.txt)",
                   "Exit"]
        self.menu_options.set(options[0])
        self.drop_menu = OptionMenu(self.root, self.menu_options, *options, command=self.menu_selection)
        self.drop_menu.config(width=10)

    def menu_selection(self, selection):
        if selection == "Exit":
            self.root.quit()
        elif selection == "Save":
            self.save_graph()
            pass
        elif selection == "Save As":
            self.save_graph_as()
        elif selection == "Export (.txt)":
            # export data into a .txt file
            pass
    
    def save_graph(self):
        '''
        Saves the current graph image with a default file name.
        '''
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        default_filename = os.path.join(downloads_folder, "graph.png")
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
            
# class for graph in homepage
class GraphGUI:
    def __init__(self, root):
        self.root = root
        self.create_graph()
        
    def create_graph(self):
        # Create a figure
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Tunneling Current (nA)')
        
        # Create a canvas to embed the figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=0, column=3, columnspan=6, rowspan=10, padx=10, pady=5)


if __name__ == "__main__":
    root_gui = RootGUI()
    root_gui.root.mainloop()