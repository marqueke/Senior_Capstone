# iv_window.py

# imported python packages
from tkinter import *
from tkinter import messagebox, filedialog
from PIL import Image
import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import os, struct, time, csv

# imported custom classes
import globals
from SPI_Data_Ctrl import SerialCtrl
from ztmSerialCommLibrary import ztmCMD, ztmSTATUS, usbMsgFunctions
from value_conversion import Convert

curr_data = 0
vb_V = 0

class IVWindow:
    def __init__(self, root, port):
        """
        Initialize the IVWindow class which sets up the GUI for acquiring I-V measurements.

        Args:
            root (tkinter.Tk): The root window of the application.
            port (str or None): The serial port to which the device is connected. If None, it indicates no connection.
        """
        self.root = root
        self.port = port
        
        # Check if a serial connection has been established when opening the window
        if self.port == None:
            messagebox.showerror("INVALID", f"No serial connection detected.\nConnect to USB via homepage and try again.") 
            self.root.destroy()
            
        self.root.title("Acquire I-V")
        self.root.config(bg="#b1ddf0")
        self.root.geometry("800x650")   # (width x length)
        
        # initialize serial control
        self.serial_ctrl = SerialCtrl(self.port, globals.BAUDRATE)
        self.ztm_serial = usbMsgFunctions(self)
        
        # Initialize the widgets
        self.init_meas_widgets()
        self.init_parameters()
        self.init_graph_widgets()
        self.update_label()
    

    def start_reading(self):
        """
        Starts reading bias voltage and current from the MCU.
        """
        print("Starting to read data...")
        if self.serial_ctrl:
            print("Serial controller is initialized, starting now...")
            checked = self.check_sweep_params()
            if checked:
                self.disable_widgets()
                self.run_bias_sweep_process()
            else:
                print("Sweep Parameters invalid. Process not started.")
        else:
            print("Serial controller is not initialized.")
    
    
    def stop_reading(self):
        """
        Disables the reading of data through the serial port.
        """
        print("Stopped reading data...")
        self.enable_widgets()
        self.STOP_BTN_FLAG = 1
        self.serial_ctrl.stop() 
    

    def init_meas_widgets(self):
        """
        Initializes widgets needed.
        """
        # current
        self.frame1 = LabelFrame(self.root, text="Current (nA)", padx=10, pady=2, bg="gray")
        self.label1 = Label(self.frame1, bg="white", width=25)
        
        # sample bias voltage
        self.frame2 = LabelFrame(self.root, text="Sample Bias Voltage (V)", padx=10, pady=2, bg="gray")
        self.label2 = Label(self.frame2, bg="white", width=25)
        
        # IV sweep voltage parameters
        # min voltage
        self.frame3 = LabelFrame(self.root, text="Minimum Voltage (V)", padx=10, pady=2, bg="#ADD8E6")
        self.label3 = Entry(self.frame3, bg="white", width=30)
        self.label3.bind("<Return>", self.saveMinVoltage)
        
        # max voltage
        self.frame4 = LabelFrame(self.root, text="Maximum Voltage (V)", padx=10, pady=2, bg="#ADD8E6")
        self.label4 = Entry(self.frame4, bg="white", width=30)
        self.label4.bind("<Return>", self.saveMaxVoltage)
        
        # number of setpoints
        self.frame6 = LabelFrame(self.root, text="Number of Setpoints", padx=10, pady=2, bg="#ADD8E6")
        self.label8 = Entry(self.frame6, bg="white", width=30)
        self.label8.bind("<Return>", self.saveNumSetpoints)
        
        # user notes text box
        self.frame5 = LabelFrame(self.root, text="NOTES", padx=10, pady=5, bg="#A7C7E7")
        self.label5 = Text(self.frame5, height=7, width=30)
        self.label5.bind("<Return>", self.save_notes)
        self.label6 = Entry(self.frame5, width=10)
        self.label6.bind("<Return>", self.save_date)
        self.label7 = Label(self.frame5, padx=10, text="Date:", height=1, width=5)

        # init buttons
        self.add_btn_image1 = ctk.CTkImage(Image.open("Images/Start_Btn.png"), size=(90,35))
        self.add_btn_image2 = ctk.CTkImage(Image.open("Images/Stop_Btn.png"), size=(90,35))
        self.add_btn_image4 = ctk.CTkImage(Image.open("Images/Start_LED.png"), size=(35,35))
        self.add_btn_image5 = ctk.CTkImage(Image.open("Images/Stop_LED.png"), size=(35,35))
																						   
        self.start_btn = ctk.CTkButton(self.root, image=self.add_btn_image1, text="", width=90, height=35, fg_color="#b1ddf0", bg_color="#b1ddf0", corner_radius=0, command=self.start_reading)
        self.stop_btn = ctk.CTkButton(self.root, image=self.add_btn_image2, text="", width=90, height=35, fg_color="#b1ddf0", bg_color="#b1ddf0", corner_radius=0, command=self.stop_reading)																																	   
        self.green_LED = ctk.CTkLabel(self.root, image=self.add_btn_image4, text="", width=35, height=35, fg_color="#b1ddf0", bg_color="#b1ddf0", corner_radius=0)
        self.red_LED = ctk.CTkLabel(self.root, image=self.add_btn_image5, text="", width=35, height=35, fg_color="#b1ddf0", bg_color="#b1ddf0", corner_radius=0)
        
        # setup the drop option menu
        self.DropDownMenu()
        
        # optional graphic parameters
        self.padx = 10
        self.pady = 10
        
        # put on the grid all the elements
        self.publish_meas_widgets()
    

    def publish_meas_widgets(self):
        """
        Method to publish needed widgets.
        """
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
        
        # positioning of the start/stop buttons and LED indicator
        self.start_btn.grid(row=1, column=10, padx=5, pady=15, sticky="s")
        self.stop_btn.grid(row=2, column=10, padx=5, sticky="n")
        self.red_LED.grid(row=1, column=11, padx=5, pady=15, sticky="s")
        

    def init_parameters(self):
        """
        This initializes all class variables.
        """
        self.min_voltage = None
        self.max_voltage = None
        self.num_setpoints = None
        self.bias_volt_range = None
        self.volt_per_step = None
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
        """
        Function to save the user input minimum voltage parameter for voltage sweep
        """
        self.root.focus()
        if self.isValidBiasInput(self.label3.get()):
            if globals.VBIAS_MIN <= float(self.label3.get()) <= globals.VBIAS_MAX:
                self.min_voltage = float(self.label3.get())
                print(f"Saved min voltage value: {self.min_voltage}")
            else:
                messagebox.showerror("INVALID", f"Invalid range. Stay within -10 to 10 V.")
        else:
            messagebox.showerror("INVALID", f"Invalid Min Voltage. Please update your parameters.")    


    def saveMaxVoltage(self, event):
        """
        Function to save the user input maximum voltage parameter for voltage sweep
        """
        self.root.focus()
        if self.isValidBiasInput(self.label4.get()):
            if globals.VBIAS_MIN <= float(self.label4.get()) <= globals.VBIAS_MAX:
                self.max_voltage = float(self.label4.get())
                print(f"Saved max voltage value: {self.max_voltage}")
            else:
                messagebox.showerror("INVALID", f"Invalid range. Stay within -10 to 10 V.")
        else:
            messagebox.showerror("INVALID", f"Invalid Max Voltage. Please update your parameters.")
    

    def isValidBiasInput(self, text):
        """
        Function to validate the user input for min and max voltage values
        """
        try:
            float(text)
            return True
        except ValueError:
            return False
    

    def saveNumSetpoints(self, event):
        """
        Function to save the user input number of data points in the voltage sweep
        """
        self.root.focus()
        if self.isValidSetpointInput(self.label8.get()):
            self.num_setpoints = int(self.label8.get())
            print(f"Saved number of setpoints value: {self.num_setpoints}")
            self.root.focus()
        else:
            messagebox.showerror("INVALID", "Invalid input. Please enter an integer.")
    

    def isValidSetpointInput(self, text):
        """
        Function to validate the user input for number of setpoints
        """
        try:
            int(text)
            return True
        except ValueError:
            return False


    def update_label(self):   
        """
        Function to update the display labels with values obtained from the microscope/microcontroller
        """ 
        global curr_data    
        global vb_V 
        self.label2.configure(text=f"{vb_V:.3f} V") # bias voltage
        self.label1.configure(text=f"{curr_data:.3f} nA") # current


    def get_current_label1(self):
        """
        Function to gather the current value, used to display data on graph and save into data array, to be exported
        """
        current_value = float(self.label1.cget("text").split()[0])  # assuming label1 text value is "value" nA
        return current_value
    

    def check_sweep_params(self):
        """
        Function to validate all user inputs before the sweep process begins
        """
        if self.min_voltage == None or self.min_voltage < globals.VBIAS_MIN or self.min_voltage > globals.VBIAS_MAX:
            messagebox.showerror("INVALID", f"Invalid minimum voltage value. Please update your parameters.")
            return False
            
        if self.max_voltage == None or self.max_voltage < globals.VBIAS_MIN or self.max_voltage > globals.VBIAS_MAX:
            messagebox.showerror("INVALID", f"Invalid maximum voltage value. Please update your paremeters.") 
            return False

        if self.num_setpoints == None or self.num_setpoints < globals.NUM_SETPOINTS_MIN:
            messagebox.showerror("INVALID", f"Invalid number of setpoints value. Please update your paremeters.") 
            return False

        self.bias_volt_range = self.max_voltage - self.min_voltage
        self.volt_per_step = self.bias_volt_range / self.num_setpoints

        if self.bias_volt_range <= 0:
            messagebox.showerror("INVALID", f"Invalid sweep range. Max value must be higher than Min value.") 
            return False
        
        if self.volt_per_step < globals.IV_VOLTS_PER_STEP_MIN:
            messagebox.showerror("INVALID", f"Invalid Step Size.\nStep size: {self.volt_per_step:.6f}\nStep size needs to be greater than or equal {globals.IV_VOLTS_PER_STEP_MIN} V ({globals.IV_VOLTS_PER_STEP_MIN*1000} mV)\nDecrease number of points or increase voltage range.") 
            return False
        
        return True


    def run_bias_sweep_process(self):
        """
        Function to run a piezo voltage sweep from the user input minimum to maximum voltages, with the number of setpoints evenly spaced in the voltage range
        """
        global vb_V
        GREEN = 1
        RED = 0
        self.change_LED(GREEN)

        # starting point for bias sweep, set to user-input minimum voltage
        self.vbias = self.min_voltage

        # enable plot interative mode
        self.reset_graph()
        plt.ion()

        for i in range(0, self.num_setpoints + 1):

            if self.STOP_BTN_FLAG == 1:
                break            

            # sending vbias to MCU, looking for a DONE status in return
            success = self.send_msg_retry(self.port, globals.MSG_A, ztmCMD.CMD_SET_VBIAS.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_DONE.value, 0, self.vbias, 0)
            if not success:
                messagebox.showerror("INVALID", f"Could not verify communication with MCU.\nSweep process aborted.") 
                self.sweep_finished()
                return
            
            # sending a REQUEST_FOR_DATA command to MCU to receive current and vbias measurements
            dataSuccess = self.send_msg_retry(self.port, globals.MSG_C, ztmCMD.CMD_REQ_DATA.value, ztmSTATUS.STATUS_CLR.value, ztmSTATUS.STATUS_MEASUREMENTS.value)
            if not dataSuccess:
                messagebox.showerror("INVALID", f"Did not receive data from MCU.\nSweep process aborted.") 
                self.sweep_finished()
                return

            # updates labels with measurements received from MCU
            self.update_label()

            if i > globals.SWEEP_GRAPH_X_AXIS_DISPLAY_NUMBER_OF_POINTS:
                self.adjusted_x_axis = vb_V - (globals.SWEEP_GRAPH_X_AXIS_DISPLAY_NUMBER_OF_POINTS * self.volt_per_step)

            # updates graph display
            self.update_graph(vb_V)

            # increment the bias voltage for the sweep
            self.vbias += self.volt_per_step

        self.sweep_finished()


    def sweep_finished(self):
        """
        Function to tidy up the conclusion of the sweep function and re-enables all widgets.
        """
        if self.STOP_BTN_FLAG == 1:
            self.change_LED(RED)
            # display message to user if sweep is aborted
            messagebox.showwarning("STOP BUTTON PRESSED", f"The voltage sweep has been STOPPED.")
        else: 
            self.change_LED(RED)
            # display message to user if sweep completed
            messagebox.showinfo("Successful Sweep", f"The voltage sweep has completed.")

        # disable plot interative mode
        plt.ioff()
        # # reset button states
        RED = 0
        self.change_LED(RED)
        self.enable_widgets()
        self.serial_ctrl.stop()
        self.STOP_BTN_FLAG = 0


    def send_msg_retry(self, port, msg_type, cmd, status, status_response, *params, max_attempts=globals.SWEEP_MAX_ATTEMPTS, sleep_time=globals.HALF_SECOND):
        '''
        Function to send a message to the MCU and retry if we do
        not receive expected response
        '''
        global curr_data
        global vb_V
        
        attempt = 0
        
        msg_print = [msg_type, cmd, status]
        
        # Convert each element in msg_print to a hex string
        msg_print_hex = ' '.join(format(x, '02X') for x in msg_print)
        
        print(f"\nMESSAGE BEING SENT: {msg_print_hex}")
        
        while attempt < max_attempts:
            print(f"\n========== ATTEMPT NUMBER: {attempt+1} ==========")
            if msg_type == globals.MSG_A:
                self.ztm_serial.sendMsgA(port, cmd, status, *params)
            elif msg_type == globals.MSG_B:
                self.ztm_serial.sendMsgB(port, cmd, status, *params)
            elif msg_type == globals.MSG_C:
                self.ztm_serial.sendMsgC(port, cmd, status, *params)
            elif msg_type == globals.MSG_D:
                self.ztm_serial.sendMsgD(port, cmd, status, *params)
            elif msg_type == globals.MSG_E:
                self.ztm_serial.sendMsgE(port, cmd, status, *params)
            else:
                raise ValueError(f"Unsupported message type: {msg_type}")
            
            # returns 11 bytes of payload FALSE or byte response
            testMsg = self.serial_ctrl.ztmGetMsg(port)
            
            testMsg_hex = [b for b in testMsg]
            
            print(f"Serial response: {testMsg_hex}")
            
            ### Unpack data and display on the GUI
            if testMsg:
                if testMsg_hex[2] == status_response and len(testMsg) == globals.MSG_BYTES:
                    unpackResponse = self.ztm_serial.unpackRxMsg(testMsg)
                    print(f"Received correct status response from MCU: {testMsg[2]}")
                    
                    if unpackResponse:
                        if testMsg_hex[2] == ztmSTATUS.STATUS_MEASUREMENTS.value:
                            curr_data = round(struct.unpack('f', bytes(testMsg[3:7]))[0], 3) #unpack bytes & convert
                            cStr = str(curr_data)  # format as a string
                            print("Received values\n\tCurrent: " + cStr + " nA\n")
                            
                            # vbias    
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
            """
            Function to save the optional user input notes box to be attached to the .csv file when exporting data
            """
            self.root.focus()
            note = self.label5.get(1.0, ctk.END)
            note = note.strip()
            return note
    

    def save_date(self, _=None):
            """
            Function to save the optional user input date box to be attached to the .csv file when exporting data
            """
            self.root.focus()
            date = self.label6.get()
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
        self.filemenu.add_command(label="Export (.txt)", command=self.export_data)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.exit_application)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.root.config(menu=self.menubar)
    

    def save_graph(self):
        """
        Function to handle the saving of the graph display into a .png file
        """
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        default_filename = os.path.join(downloads_folder, "iv_graph.png")
        self.fig.savefig(default_filename)
        messagebox.showinfo("Save Graph", f"Graph saved in Downloads as {default_filename}")
        

    def save_graph_as(self):
        """
        Function to handle the saving of the graph display into a .png file
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if file_path:
            self.fig.savefig(file_path)
            messagebox.showinfo("Save Graph As", f"Graph saved as {file_path}")
    

    def export_data(self):
        '''
        Handles the exporting of data collected into a .csv file
        ''' 
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
        '''
        Function to initialize the data arrays and the graphical display
        ''' 
        self.fig, self.ax = plt.subplots()
        self.fig.set_figwidth(7)
        self.fig.set_figheight(4.5)
        self.ax.set_xlabel('Sample Bias Voltage (V)')
        self.ax.set_ylabel('Tunneling Current (nA)')
        
        # Create a canvas to embed the figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=1, column=0, columnspan=10, rowspan=8, padx=10, pady=10)
        

    def update_graph(self, xAxisDataPoint):
        '''
        This will update the visual graph with the data points obtained during
        the Bias Voltage Sweep. The data points are appended to the data arrays.
        '''
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


    def reset_graph(self):
        '''
        Resets the visual graph and clears the data points.
        '''
        self.adjusted_x_axis = None
        self.ax.clear()
        self.ax.set_xlabel('Sample Bias Voltage (V)')
        self.ax.set_ylabel('Tunneling Current (nA)')
        self.y_data = []
        self.x_data = []
        self.line, = self.ax.plot([], [], 'r-')
        self.canvas.draw()
        self.canvas.flush_events()