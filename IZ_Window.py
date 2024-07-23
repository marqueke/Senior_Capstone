# iz_window.py

from tkinter import *
from tkinter import messagebox, filedialog
from PIL import Image
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import os, struct

from Sweep_IZ import SweepIZ_Window  # import the IZ Sweep Window Class
from SPI_Data_Ctrl import SerialCtrl
from Data_Com_Ctrl import DataCtrl
from value_conversion import Convert
from ztmSerialCommLibrary import ztmCMD, ztmSTATUS, usbMsgFunctions, MSG_A, MSG_B, MSG_C, MSG_D, MSG_E, MSG_F

class IZWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Acquire I-Z")
        self.root.config(bg="#d0cee2")
        self.root.geometry("750x675")   # (length x width)

        # initialize data and serial control
        self.data_ctrl = DataCtrl(9600, self.handle_data)
        self.serial_ctrl = SerialCtrl('COM9', 9600, self.data_ctrl.decode_data)
        
        # Initialize the widgets
        self.init_meas_widgets()
        self.init_graph_widgets()
        self.init_data_btns()
    
    def start_reading(self):
        print("Starting to read data...")
        if self.serial_ctrl:
            print("Serial controller is initialized, starting now...")
            self.serial_ctrl.start()
            self.send_parameters()
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

    def send_parameters(self):

        vpzo_min = self.get_float_value(self.label4, 0.0, "Voltage Piezo Minimum")
        vpzo_max = self.get_float_value(self.label5, 0.0, "Voltage Piezo Maximum")

        # convert vpzo to int
        vpzo_min_int = Convert.get_Vpiezo_int(vpzo_min)
        vpzo_max_int = Convert.get_Vpiezo_int(vpzo_max)
        
        print(f"Vpzo min int: {vpzo_min_int}, Vpzo max int: {vpzo_max_int}")
        
        # convert values to bytes
        vpzo_min_bytes = struct.pack('>H', vpzo_min_int)
        vpzo_max_bytes = struct.pack('>H', vpzo_max_int)
        
        
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
        
        # IV sweep voltage parameters
        # min voltage
        self.frame4 = LabelFrame(self.root, text="Minimum Piezo Voltage (V)", padx=10, pady=2, bg="#A7C7E7")
        self.label4 = Entry(self.frame4, bg="white", width=30)
        
        # max voltage
        self.frame5 = LabelFrame(self.root, text="Maximum Piezo Voltage (V)", padx=10, pady=2, bg="#A7C7E7")
        self.label5 = Entry(self.frame5, bg="white", width=30)
    
        # number of setpoints
        self.frame7 = LabelFrame(self.root, text="Number of Setpoints", padx=10, pady=2, bg="#A7C7E7")
        self.label9 = Entry(self.frame7, bg="white", width=30)

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
    
    def init_data_btns(self):
        self.add_btn_image1 = ctk.CTkImage(Image.open("Images/Start_Btn.png"), size=(90,35))
        self.add_btn_image2 = ctk.CTkImage(Image.open("Images/Stop_Btn.png"), size=(90,35))
        self.add_btn_image3 = ctk.CTkImage(Image.open("Images/Start_LED.png"), size=(35,35))
        self.add_btn_image4 = ctk.CTkImage(Image.open("Images/Stop_LED.png"), size=(35,35))
        
        self.start_btn = ctk.CTkButton(self.root, image=self.add_btn_image1, text="", width=90, height=35, fg_color="#d0cee2", bg_color="#d0cee2", corner_radius=0, command=self.start_reading)
        self.stop_btn = ctk.CTkButton(self.root, image=self.add_btn_image2, text="", width=90, height=35, fg_color="#d0cee2", bg_color="#d0cee2", corner_radius=0, command=self.stop_reading)
        self.start_led_btn = ctk.CTkButton(self.root, image=self.add_btn_image3, text="", width=35, height=35, fg_color="#d0cee2", bg_color="#d0cee2", corner_radius=0)
        self.stop_led_btn = ctk.CTkButton(self.root, image=self.add_btn_image4, text="", width=35, height=35, fg_color="#d0cee2", bg_color="#d0cee2", corner_radius=0)
        
        self.publish_data_btns()
        
    def publish_data_btns(self):
        self.start_btn.grid(row=1, column=10, padx=5, pady=15, sticky="s")
        self.stop_btn.grid(row=2, column=10, padx=5, sticky="n")
        self.stop_led_btn.grid(row=1, column=11, padx=5, pady=15, sticky="sw")
        # need to switch RG LED on process state
        #self.start_led_btn.grid(row=1, column=11, padx=5, pady=15, sticky="sw")

    def saveMinVoltage(self, event):
        self.min_voltage = self.label4.get()
        print(f"Saved min voltage value: {self.min_voltage}")

    def saveMaxVoltage(self, event):
        self.max_voltage = self.label5.get()
        print(f"Saved max voltage value: {self.max_voltage}")

    def saveNumSetpoints(self, event):
        self.num_setpoints = self.label9.get()
        print(f"Saved number of setpoints value: {self.num_setpoints}")

    def run_sweep_process(self):
        volt_per_step = self.max_voltage - self.min_voltage
        volt_per_step = volt_per_step / self.num_setpoints

        #starting point for piezo sweep
        self.vpiezo = self.min_voltage
        self.parent.ztm_serial.sendMsgA(self.parent.serial_ctrl.serial_port, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_MEASUREMENTS.value, 0, 0, vpiezo)

        for i in range(0, self.num_setpoints - 1):
            self.parent.ztm_serial.sendMsgA(self.parent.serial_ctrl.serial_port, ztmCMD.CMD_PIEZO_ADJ.value, ztmSTATUS.STATUS_MEASUREMENTS.value, 0, 0, vpiezo)

            # read done message receieved from mcu
            ack_response = self.parent.serial_ctrl.read_bytes()
            # looking for ACK message from MCU
            if ack_response:
                print(f"Response recieved: {ack_response}")
                status_received = self.parent.ztm_serial.unpackRxMsg(ack_response)

                # looking for STATUS.ACK
                if status_received != ztmSTATUS.STATUS_ACK.value:
                    print(f"ERROR: wrong status recieved, status value: {status_received}")   
                    print("STOPPING SWEEP PROCESS")
                    break
                else:
                    print(f"Response recieved: {status_received}")
            else:
                print("Failed to receive response from MCU.")

            self.vpiezo += volt_per_step
            self.num_setpoints += 1
        
    # currently working on this **********************************************************
    # current, piezo voltage, piezo extension
    def update_label(self):
        self.label1.configure(text=f"{self.piezo_distance:.3f} nm") # piezo extension
        self.label2.configure(text=f"{self.vpiezo:.3f} nA") # piezo voltage
        self.label3.configure(text=f"{self.adc_curr:.3f} nA") # current

        self.label2.after(1000, self.update_label)

        
    # def open_iz_sweep_window(self):
    #     '''
    #     Method to open a new window when the "Piezo Sweep Parameters" button is clicked
    #     '''
    #     new_window = ctk.CTkToplevel(self.root)
    #     SweepIZ_Window(new_window)
    
    def return_home(self):
        self.root.destroy()
        
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
            self.root.destroy()
        elif selection == "Save":
            self.save_graph()
        elif selection == "Save As":
            self.save_graph_as()
        elif selection == "Export (.txt)":
            self.export_data()
    
    def save_graph(self):
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        default_filename = os.path.join(downloads_folder, "graph.png")
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
