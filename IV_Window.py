# iv_window.py

from tkinter import *
from tkinter import messagebox, filedialog
from PIL import Image
import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import os, struct, time
import csv

from Sweep_IV import SweepIV_Window  # import the IV Sweep Window Class
from SPI_Data_Ctrl import SerialCtrl
from Data_Com_Ctrl import DataCtrl
from value_conversion import Convert
from ztmSerialCommLibrary import ztmCMD, ztmSTATUS, usbMsgFunctions, MSG_A, MSG_B, MSG_C, MSG_D, MSG_E

curr_data = 0
vb_V = 0

class IVWindow:
    def __init__(self, root, port):
        self.root = root
        self.port = port
        
        # Check if a serial connection has been established when opening the window
        if self.port == None:
            messagebox.showerror("INVALID", f"No serial connection detected.\nConnect to USB via homepage and try again.") 
            self.root.destroy()
            
        self.root.title("Acquire I-V")
        self.root.config(bg="#b1ddf0")
        self.root.geometry("750x675")   # (length x width)
        
        # initialize data and serial control
        self.data_ctrl = DataCtrl(460800, self.handle_data)
        self.serial_ctrl = SerialCtrl('COM9', 460800, self.data_ctrl.decode_data)
        
        #self.data_ctrl.set_serial_ctrl(self.serial_ctrl)
        self.ztm_serial = usbMsgFunctions(self)
        
        # Initialize the widgets
        self.init_meas_widgets()
        self.init_parameters()
        self.init_graph_widgets()
        
        self.vbias = 0
        self.current = 0
    
    def start_reading(self):
        print("Starting to read data...")
        if self.serial_ctrl:
            print("Serial controller is initialized, starting now...")
            #self.serial_ctrl.start()
            checked = self.check_sweep_params()
            if checked:
                self.disable_widgets()
                self.run_bias_sweep_process()
            else:
                print("Sweep Parameters invalid. Process not started.")
            #self.send_parameters()
        else:
            print("Serial controller is not initialized.")
    
    
    def stop_reading(self):
        print("Stopped reading data...")
        self.enable_widgets()
        self.STOP_BTN_FLAG = 1
        self.serial_ctrl.stop() # need to change later
    
    def handle_data(self, raw_data):
        print(f"Handling raw data: {raw_data.hex()}")
        decoded_data = self.data_ctrl.decode_data(raw_data)
        if decoded_data:
            print("Data is being decoded...")
            adc_curr, vbias, vpzo = decoded_data
            self.update_vbias(vbias)
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

    def send_parameters(self, port):
        # get vbias min/max and num setpoints from user input
        vbias_min = self.get_float_value(self.label3, 0.0, "Voltage Bias Minimum")
        vbias_max = self.get_float_value(self.label4, 0.0, "Voltage Bias Maximum")
        num_setpoints = self.get_float_value(self.label8, 10.0, "Number of Setpoints")
        
        # convert vbias and setpoints to int
        vbias_min_int = Convert.get_Vbias_int(vbias_min)
        vbias_max_int = Convert.get_Vbias_int(vbias_max)
        num_setpoints_int = int(num_setpoints)
        
        # calculate delta
        delta = (vbias_max_int - vbias_min_int) / num_setpoints_int
        
        # set to minimum vbias
        tempVbias = vbias_min_int
        i = 0
        
        # BACK AND FORTH
        while num_setpoints >= i:
            pass
            #self.parent.ztm_serial.sendMsgA(port, ztmCMD.CMD_SET_VBIAS.value, ztmSTATUS.STATUS_MEASUREMENTS.value, 0, tempVbias, 0)
        
        # send msg to MCU
        
        
        self.label2.configure(text=f"{self.vbias:.3f} V")
        self.label1.configure(text=f"{self.current:.3f} nA")
        #time.sleep(1)
        #self.label2.configure(text=f"{self.vbias:.3f} V")
        
        '''
        print(f"Vbias min int: {vbias_min_int}, Vbias max int: {vbias_max_int}")
        
        # convert values to bytes
        vbias_min_bytes = struct.pack('>H', vbias_min_int)
        vbias_max_bytes = struct.pack('>H', vbias_max_int)
        
        
        # Construct the payload with vpzo in the correct position
        payload_min = vbias_min_bytes
        payload_max = vbias_max_bytes
        
        print(f"Payload Vbias Minimum: {payload_min.hex()}")
        print(f"Payload Vbias Maximum: {payload_max.hex()}")
        
    
        # SAVING BC UNSURE ABOUT VBIAS
        self.data_ctrl.send_command(MSG_A, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_DONE.value, payload_min)
        
        response = self.serial_ctrl.read_serial_blocking()
        if response:
            print(f"MCU Response: {response.hex()}")
        else:
            print("No response received from MCU")
        '''
        
        '''
        ##### WRITE TO DISPLAY DATA AFTER RECEIVING A RESPONSE #####
        vb_V = round(self.get_Vbias_float_V(struct.unpack('H',bytes(testMsg[7:9]))[0]), 3) #unpack bytes & convert
        vbStr = str(vb_V)   # format as a string
        print("\tVbias: " + vbStr + " V\n")
        '''

            
    def init_meas_widgets(self):
        # current
        self.frame1 = LabelFrame(self.root, text="Current (nA)", padx=10, pady=2, bg="gray")
        self.label1 = Label(self.frame1, bg="white", width=25)
        
        # sample bias voltage
        self.frame2 = LabelFrame(self.root, text="Sample Bias Voltage (V)", padx=10, pady=2, bg="gray")
        self.label2 = Label(self.frame2, bg="white", width=25)
        
        # IV sweep voltage parameters
        # min voltage
        self.frame3 = LabelFrame(self.root, text="Minimum Voltage (V)", padx=10, pady=2, bg="#A7C7E7")
        self.label3 = Entry(self.frame3, bg="white", width=30)
        self.label3.bind("<Return>", self.saveMinVoltage)
        
        # max voltage
        self.frame4 = LabelFrame(self.root, text="Maximum Voltage (V)", padx=10, pady=2, bg="#A7C7E7")
        self.label4 = Entry(self.frame4, bg="white", width=30)
        self.label4.bind("<Return>", self.saveMaxVoltage)
        
        # number of setpoints
        self.frame6 = LabelFrame(self.root, text="Number of Setpoints", padx=10, pady=2, bg="#A7C7E7")
        self.label8 = Entry(self.frame6, bg="white", width=30)
        self.label8.bind("<Return>", self.saveNumSetpoints)
        
        # user notes text box
        self.frame5 = LabelFrame(self.root, text="NOTES", padx=10, pady=5, bg="#A7C7E7")
        self.label5 = Text(self.frame5, height=7, width=30)
        self.label5.bind("<Return>", self.save_notes)
        self.label6 = Entry(self.frame5, width=10)
        self.label6.bind("<Return>", self.save_date)
        self.label7 = Label(self.frame5, padx=10, text="Date:", height=1, width=5)

        self.add_btn_image1 = ctk.CTkImage(Image.open("Images/Start_Btn.png"), size=(90,35))
        self.add_btn_image2 = ctk.CTkImage(Image.open("Images/Stop_Btn.png"), size=(90,35))
        #self.add_btn_image3 = ctk.CTkImage(Image.open("Images/Homepage_Btn.png"), size=(90,35))
        self.add_btn_image4 = ctk.CTkImage(Image.open("Images/Start_LED.png"), size=(35,35))
        self.add_btn_image5 = ctk.CTkImage(Image.open("Images/Stop_LED.png"), size=(35,35))
																						   
        
        self.start_btn = ctk.CTkButton(self.root, image=self.add_btn_image1, text="", width=90, height=35, fg_color="#b1ddf0", bg_color="#b1ddf0", corner_radius=0, command=self.start_reading)
        self.stop_btn = ctk.CTkButton(self.root, image=self.add_btn_image2, text="", width=90, height=35, fg_color="#b1ddf0", bg_color="#b1ddf0", corner_radius=0, command=self.stop_reading)
        #self.home_btn = ctk.CTkButton(self.root, image=self.add_btn_image3, text="", width=90, height=35, fg_color="#b1ddf0", bg_color="#b1ddf0", corner_radius=0, command=self.return_home)																																				   
        self.green_LED = ctk.CTkLabel(self.root, image=self.add_btn_image4, text="", width=35, height=35, fg_color="#d0cee2", bg_color="#d0cee2", corner_radius=0)
        self.red_LED = ctk.CTkLabel(self.root, image=self.add_btn_image5, text="", width=35, height=35, fg_color="#d0cee2", bg_color="#d0cee2", corner_radius=0)
        
        # setup the drop option menu
        self.DropDownMenu()
        
        # optional graphic parameters
        self.padx = 10
        self.pady = 10
        
        # put on the grid all the elements
        self.publish_meas_widgets()
    
    def publish_meas_widgets(self):
        # current
        self.frame1.grid(row=12, column=0, padx=5, pady=5, sticky="e")
        self.label1.grid(row=0, column=0, padx=5, pady=5)
        
        # sample bias voltage
        self.frame2.grid(row=12, column=1, padx=5, pady=5, sticky="e")
        self.label2.grid(row=0, column=0, padx=5, pady=5)   
        
        # min voltage
        self.frame3.grid(row=11, column=0, padx=5, pady=5, sticky="n")
        self.label3.grid(row=0, column=0, padx=5, pady=5)
        
        # max voltage
        self.frame4.grid(row=11, column=1, padx=5, pady=5, sticky="n")
        self.label4.grid(row=0, column=0, padx=5, pady=5)

        # number of setpoints
        self.frame6.grid(row=13, column=0, padx=5, pady=5, sticky="e")
        self.label8.grid(row=0, column=0, padx=5, pady=5)

        # Positioning the notes section
        self.frame5.grid(row=11, column=7, rowspan=3, pady=5, sticky="n")
        self.label5.grid(row=1, column=0, pady=5, columnspan=3, rowspan=3) 
        self.label6.grid(row=0, column=2, pady=5, sticky="e")
        self.label7.grid(row=0, column=2, pady=5, sticky="w")
        
        self.start_btn.grid(row=1, column=10, padx=5, pady=15, sticky="s")
        self.stop_btn.grid(row=2, column=10, padx=5, sticky="n")
        #self.home_btn.grid(row=15, column=10, sticky="n")
        self.red_LED.grid(row=1, column=11, padx=5, pady=15, sticky="s")

    def return_home(self):
        self.root.destroy()
        
    def init_parameters(self):
        self.min_voltage = None
        self.max_voltage = None
        self.num_setpoints = None
        self.bias_volt_range = None
        self.volt_per_step = None
        self.random_num = 0
        self.adjusted_x_axis = None
        self.STOP_BTN_FLAG = 0

    def disable_widgets(self):
        """
        Function to disable entry widgets when we start seeking.
        Disabling:
            - min voltage
            - max voltage
            - number of setpoints
            - start button
            - stop button
        """
        self.label3.configure(state="disabled")
        self.label4.configure(state="disabled")
        self.label8.configure(state="disabled")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

    def enable_widgets(self):
        """
        Function to enable entry widgets when the process is stopped.
        Enabling:
            - min voltage
            - max voltage
            - number of setpoints
            - start button
            - stop button
        """
        self.label3.configure(state="normal")
        self.label4.configure(state="normal")
        self.label8.configure(state="normal")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        
    def saveMinVoltage(self, event):
        self.root.focus()
        if -10 <= float(self.label3.get()) <= 10:
            self.min_voltage = float(self.label3.get())
            print(f"Saved min voltage value: {self.min_voltage}")
        else:
            messagebox.showerror("INVALID", f"Invalid range. Stay within -10 to 10 V.")

    def saveMaxVoltage(self, event):
        self.root.focus()
        if -10 <= float(self.label4.get()) <= 10:
            self.max_voltage = float(self.label4.get())
            print(f"Saved min voltage value: {self.max_voltage}")
        else:
            messagebox.showerror("INVALID", f"Invalid range. Stay within -10 t0 10 V.") 

    def saveNumSetpoints(self, event):
        self.root.focus()
        self.num_setpoints = int(self.label8.get())
        print(f"Saved number of setpoints value: {self.num_setpoints}")
        
    def change_LED(self, color):
        if color == 0:
            self.green_LED.grid_remove()
            self.red_LED.grid(row=1, column=11, padx=5, pady=15, sticky="sw")
        elif color == 1:
            self.red_LED.grid_remove()
            self.green_LED.grid(row=1, column=11, padx=5, pady=15, sticky="sw")

    '''
    # update vbias
    def update_vbias(self, vbias):
        vbias_str = str(vbias)
        self.label2.config(text=vbias_str)
    '''
        
    # current and piezo voltage
    def update_label(self):   
        global curr_data     
        self.label2.configure(text=f"{vb_V:.3f} V") # piezo voltage
        self.label1.configure(text=f"{curr_data:.3f} nA") # current

    def get_current_label1(self):
        current_value = float(self.label1.cget("text").split()[0])  # assuming label1 text value is "value" nA
        return current_value
    
    def check_sweep_params(self):
        if self.min_voltage == None or self.min_voltage < -10 or self.min_voltage > 10:
            messagebox.showerror("INVALID", f"Invalid Min Voltage. Please update your paremeters.")
            return False
        
        if self.max_voltage == None or self.max_voltage <= -10 or self.max_voltage > 10:
            messagebox.showerror("INVALID", f"Invalid Max Voltage. Please update your paremeters.") 
            return False

        if self.num_setpoints == None or self.num_setpoints <= 0:
            messagebox.showerror("INVALID", f"Invalid Number of Setpoints. Please update your paremeters.") 
            return False

        self.bias_volt_range = self.max_voltage - self.min_voltage
        self.volt_per_step = self.bias_volt_range / self.num_setpoints

        if self.bias_volt_range <= 0:
            messagebox.showerror("INVALID", f"Invalid sweep range. Max value must be higher than Min value.") 
            return False
        
        if self.volt_per_step < 0.0002:
            messagebox.showerror("INVALID", f"Invalid Step Size.\nStep size: {self.volt_per_step:.6f}\nStep size needs to be greater than or equal 0.0002V (0.2 mV)\nDecrease number of points or increase voltage range.") 
            return False
        
        return True

    def run_bias_sweep_process(self):
        global vb_V
        GREEN = 1
        RED = 0
        self.change_LED(GREEN)

        # starting point for bias sweep, set to user-input minimum voltage
        self.vbias = self.min_voltage

        # enable plot interative mode
        self.reset_graph()
        plt.ion()

        # while self.STOP_BTN_FLAG == 0:
        for i in range(0, self.num_setpoints + 1):

            if self.STOP_BTN_FLAG == 1:
                break            

            # sending vbias to MCU, looking for a DONE status in return
            success = self.send_msg_retry(self.port, MSG_A, ztmCMD.CMD_SET_VBIAS.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 0, self.vbias, 0)
            if not success:
                messagebox.showerror("INVALID", f"Could not verify communication with MCU.\nSweep process aborted.") 
                self.sweep_finished()
                return
            
            # sending a REQUEST_FOR_DATA command to MCU to receive current and vpiezo measurements
            dataSuccess = self.send_msg_retry(self.port, MSG_C, ztmCMD.CMD_REQ_DATA.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_MEASUREMENTS.value)
            if not dataSuccess:
                messagebox.showerror("INVALID", f"Did not receive data from MCU.\nSweep process aborted.") 
                self.sweep_finished()
                return

            # updates labels with measurements received from MCU
            self.update_label()

            if i > self.x_axis_display_max_number_of_points:
                self.adjusted_x_axis = vb_V - (self.x_axis_display_max_number_of_points * self.volt_per_step)

            # updates graph display
            self.update_graph(vb_V)

            # increment the bias voltage for the sweep
            self.vbias += self.volt_per_step

        if self.STOP_BTN_FLAG == 1:
            self.change_LED(RED)
            # display message to user if sweep is aborted
            messagebox.showerror("STOP BUTTON PRESSED", f"The voltage sweep has been STOPPED.")
        else: 
            self.change_LED(RED)
            # display message to user if sweep completed
            messagebox.showerror("Successful Sweep", f"The voltage sweep has completed.")

        self.sweep_finished()

    def sweep_finished(self):
        # disable plot interative mode
        plt.ioff()
        # # reset button states
        RED = 0
        self.change_LED(RED)
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.STOP_BTN_FLAG = 0

    '''
    Function to send a message to the MCU and retry if we do
    not receive expected response
    '''
    def send_msg_retry(self, port, msg_type, cmd, status, status_response, *params, max_attempts=1, sleep_time=0.5):
        global curr_data
        global vb_V
        
        attempt = 0
        
        msg_print = [msg_type, cmd, status]
        
        # Convert each element in msg_print to a hex string
        msg_print_hex = ' '.join(format(x, '02X') for x in msg_print)
        
        print(f"\nMESSAGE BEING SENT: {msg_print_hex}")
        
        while attempt < max_attempts:
            print(f"\n========== ATTEMPT NUMBER: {attempt+1} ==========")
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
            
            # returns 11 bytes of payload FALSE or byte response
            testMsg = self.serial_ctrl.ztmGetMsg(port)
            #testMsg = self.parent.serial_ctrl.read_bytes()
            
            testMsg_hex = [b for b in testMsg]
            
            print(f"Serial response: {testMsg_hex}")
            
            ### Unpack data and display on the GUI
            if testMsg:
                if testMsg_hex[2] == status_response and len(testMsg) == 11:
                    unpackResponse = self.ztm_serial.unpackRxMsg(testMsg)
                    print(f"Received correct status response from MCU: {testMsg[2]}")
                    
                    if unpackResponse:
                        if testMsg_hex[2] == ztmSTATUS.STATUS_MEASUREMENTS.value:
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
            
    def save_notes(self, _=None):
            self.root.focus()
            note = self.label5.get(1.0, ctk.END)
            note = note.strip()
            return note
    
    def save_date(self, _=None):
            self.root.focus()
            date = self.label6.get()
            return date
                
    # file drop-down menu
    def DropDownMenu(self):
        self.menubar = tk.Menu(self.root)
        
        #self.custom_font = tkFont.Font(size=8)
        
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Save", command=self.save_graph)
        self.filemenu.add_command(label="Save As", command=self.save_graph_as)
        self.filemenu.add_command(label="Export (.txt)", command=self.export_data)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.exit_application)
        
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        
        self.root.config(menu=self.menubar)
    
    def save_graph(self):
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        default_filename = os.path.join(downloads_folder, "iv_graph.png")
        self.fig.savefig(default_filename)
        messagebox.showinfo("Save Graph", f"Graph saved in Downloads as {default_filename}")
        
    def save_graph_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if file_path:
            self.fig.savefig(file_path)
            messagebox.showinfo("Save Graph As", f"Graph saved as {file_path}")
    
    def export_data(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w', newline='') as file:
                # collects the user input text from the notes widget
                header_text = self.save_notes()
                header_date = self.save_date()

                # conjoining and formatting data
                headers = ["Bias Voltage (V)", "Tunneling Current (nA)"]
                data_to_export = [headers]
                data_to_export.extend(zip(self.x_data, self.y_data))

                # writing to file being created
                writer = csv.writer(file)
                # if the header notes widget has been used, include information in .csv
                if header_date:
                    writer.writerow(['Date:', header_date])
                if header_text:
                    writer.writerow(['Notes:',header_text])
                writer.writerows(data_to_export)

            messagebox.showinfo("Export Data", f"Data exported as {file_path}")
    
    def exit_application(self):
        """
        Method to handle the exit command from the drop-down menu.
        """
        self.root.destroy()
        # Re-enable the main window (homepage)
        parent_window = self.root.master
        parent_window.attributes("-disabled", False)
            
    def init_graph_widgets(self):
        self.fig, self.ax = plt.subplots()
        self.fig.set_figwidth(7)
        self.fig.set_figheight(4.5)
        
        # Create a canvas to embed the figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=1, column=0, columnspan=10, rowspan=8, padx=10, pady=10)

        # Start animation
        #self.ani = animation.FuncAnimation(self.fig, self.animate, interval=1000, cache_frame_data=False)
        
        # number of points displayed on the graph at a time, may change as desired
        self.x_axis_display_max_number_of_points = 200
        
    '''
    This will update the visual graph with the data points obtained during
    the Piezo Voltage Sweep. The data points are appended to the data arrays.
    '''
    def update_graph(self, xAxisDataPoint):
        # fetch data from label 1
        current_data = self.get_current_label1()
        
        # update data with next data points
        self.y_data.append(current_data)
        self.x_data.append(xAxisDataPoint)
        
        # update graph with new data
        self.line.set_data(self.x_data, self.y_data)
        self.ax.relim()

        # set x-axis limits for tracking data visually
        self.ax.set_xlim(self.min_voltage-0.001, vb_V)
        # if threshold for display has been hit, update x-axis limits to follow data as it updates
        if self.adjusted_x_axis != None:
           self.ax.set_xlim(self.adjusted_x_axis, vb_V)
        self.ax.autoscale_view()
        
        # redraw canvas
        self.canvas.draw()
        self.canvas.flush_events()

    '''
    Resets the visual graph and clears the data points.
    '''
    def reset_graph(self):
        self.adjusted_x_axis = None
        self.ax.clear()
        self.ax.set_xlabel('Piezo Voltage (V)')
        self.ax.set_ylabel('Tunneling Current (nA)')
        self.y_data = []
        self.x_data = []
        self.line, = self.ax.plot([], [], 'r-')
        self.canvas.draw()
        self.canvas.flush_events()
