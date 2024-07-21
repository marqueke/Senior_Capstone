# iv_window.py

from tkinter import *
from tkinter import messagebox, filedialog
from PIL import Image
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import os, struct, time

from Sweep_IV import SweepIV_Window  # import the IV Sweep Window Class
from SPI_Data_Ctrl import SerialCtrl
from Data_Com_Ctrl import DataCtrl
from value_conversion import Convert
from ztmSerialCommLibrary import ztmCMD, ztmSTATUS, usbMsgFunctions, MSG_A, MSG_B, MSG_C, MSG_D, MSG_E, MSG_F

class IVWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Acquire I-V")
        self.root.config(bg="#b1ddf0")
        self.root.geometry("755x675")   # (length x width)
        
        # initialize data and serial control
        self.data_ctrl = DataCtrl(9600, self.handle_data)
        self.serial_ctrl = SerialCtrl('COM9', 9600, self.data_ctrl.decode_data)
        self.data_ctrl.set_serial_ctrl(self.serial_ctrl)
        
        # Initialize the widgets
        self.init_meas_widgets()
        self.init_graph_widgets()
        self.init_data_btns()
        
        self.vbias = 0
        self.current = 0
    
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

    def send_parameters(self):
        testMsg = [MSG_A, 0X00, 0X00, 0X00, 0X00, 0X00, 0X00, 0x00, 0x00, 0x00, 0x00] 
        
        # values of interest
        testCurrent = 2.547895322   # Example float value to pack into bytes
        vB = 4.5                    # example vbias V from gui
        vP = 6.7                    # example vpiezo V from gui

        # Pack the floats into bytes objects
        testCurrBytes = struct.pack('f', testCurrent)
        vbiasBytes = struct.pack('H', Convert.get_Vbias_int(vB))
        vpzoBytes = struct.pack('H', Convert.get_Vpiezo_int(vP))

        # load them into the dummy message
        testMsg[3:7]  = list(testCurrBytes)
        testMsg[7:9]  = list(vbiasBytes)
        testMsg[9:11] = list(vpzoBytes)

        # Pretend we received the message - we need to decode the data for use/display
            # current
        current_nA = round(struct.unpack('f', bytes(testMsg[3:7]))[0], 3) #unpack bytes & convert
        self.current = current_nA
        cStr = str(current_nA)  # format as a string
        print("Received values\n\tCurrent: " + cStr + " nA\n")
            
        vb_V = round(Convert.get_Vbias_float(struct.unpack('H',bytes(testMsg[7:9]))[0]), 3) #unpack bytes & convert
        self.vbias = vb_V
        vbStr = str(vb_V)   # format as a string
        print("\tVbias: " + vbStr + " V\n")
        
            # vpiezo
        vp_V = round(Convert.get_Vpiezo_float(struct.unpack('H',bytes(testMsg[9:11]))[0]), 3) #unpack bytes & convert
        vpStr = str(vp_V)   # format as a string
        print("\tVpiezo: " + vpStr + " V\n")
        
        self.label2.configure(text=f"{self.vbias:.3f} V")
        self.label1.configure(text=f"{self.current:.3f} nA")
        #time.sleep(1)
        #self.label2.configure(text=f"{self.vbias:.3f} V")
        
        '''
        vbias_min = self.get_float_value(self.label3, 0.0, "Voltage Bias Minimum")
        vbias_max = self.get_float_value(self.label4, 0.0, "Voltage Bias Maximum")

        # convert vbias and vpzo to int
        vbias_min_int = Convert.get_Vbias_int(vbias_min)
        vbias_max_int = Convert.get_Vbias_int(vbias_max)
        
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
        self.frame3 = LabelFrame(self.root, text="Minimum Voltage (V)", padx=10, pady=2, bg="#ADD8E6")
        self.label3 = Entry(self.frame3, bg="white", width=30)
        
        # max voltage
        self.frame4 = LabelFrame(self.root, text="Maximum Voltage (V)", padx=10, pady=2, bg="#ADD8E6")
        self.label4 = Entry(self.frame4, bg="white", width=30)

        # number of setpoints
        self.frame6 = LabelFrame(self.root, text="Number of setpoints", padx=10, pady=2, bg="#ADD8E6")
        self.label8 = Entry(self.frame6, bg="white", width=30)

        # user notes text box
        self.frame5 = LabelFrame(self.root, text="NOTES", padx=10, pady=5, bg="#A7C7E7")
        self.label5 = Text(self.frame5, height=7, width=30)
        self.label6 = Text(self.frame5, height=1, width=8)
        self.label7 = Label(self.frame5, padx=10, text="Date:", height=1, width=5)
        
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
        
        # Positioning the file drop-down menu
        self.drop_menu.grid(row=0, column=0, padx=self.padx, pady=self.pady, sticky="w")
    
    def init_data_btns(self):
        self.add_btn_image1 = ctk.CTkImage(Image.open("Images/Start_Btn.png"), size=(90,35))
        self.add_btn_image2 = ctk.CTkImage(Image.open("Images/Stop_Btn.png"), size=(90,35))
        self.add_btn_image3 = ctk.CTkImage(Image.open("Images/Homepage_Btn.png"), size=(90,35))
        self.add_btn_image4 = ctk.CTkImage(Image.open("Images/Sweep_IV_Btn.png"), size=(90,35))
        self.add_btn_image5 = ctk.CTkImage(Image.open("Images/Stop_LED.png"), size=(35,35))
																						   
        
        self.start_btn = ctk.CTkButton(self.root, image=self.add_btn_image1, text="", width=90, height=35, fg_color="#b1ddf0", bg_color="#b1ddf0", corner_radius=0, command=self.start_reading)
        self.stop_btn = ctk.CTkButton(self.root, image=self.add_btn_image2, text="", width=90, height=35, fg_color="#b1ddf0", bg_color="#b1ddf0", corner_radius=0, command=self.stop_reading)
        self.home_btn = ctk.CTkButton(self.root, image=self.add_btn_image3, text="", width=90, height=35, fg_color="#b1ddf0", bg_color="#b1ddf0", corner_radius=0)
        self.sweep_btn = ctk.CTkButton(self.root, image=self.add_btn_image4, text="", width=90, height=35, fg_color="#b1ddf0", bg_color="#b1ddf0", corner_radius=0, command=self.open_iv_sweep_window)
																																									   
        self.stop_led_btn = ctk.CTkButton(self.root, image=self.add_btn_image5, text="", width=35, height=35, fg_color="#b1ddf0", bg_color="#b1ddf0", corner_radius=0)
        
        self.publish_data_btns()
        
    def publish_data_btns(self):
        self.start_btn.grid(row=1, column=10, padx=5, pady=15, sticky="s")
        self.stop_btn.grid(row=2, column=10, padx=5, sticky="n")
        self.stop_led_btn.grid(row=1, column=11, padx=5, pady=15, sticky="s")
        self.sweep_btn.grid(row=14, column=10, sticky="n")
        self.home_btn.grid(row=15, column=10, sticky="n")
    
    '''
    
    '''
    # update vbias
    def update_vbias(self, vbias):
        vbias_str = str(vbias)
        self.label2.config(text=vbias_str)
        
    def update_label(self):
        self.label2.configure(text=f"{self.vbias:.3f} V")
        #self.label2.delete(0, END)
        #self.label2.insert(0, f"{self.vbias:.3f}")
        #self.label3.delete(0, END)
        #self.label3.insert(0, f"{self.vpzo:.3f}")
        self.vbias = self.vbias + 1
        self.label2.after(1000, self.update_label)
        
        
    def open_iv_sweep_window(self):
        '''
        Method to open a new window when the "Piezo Sweep Parameters" button is clicked
        '''
        new_window = ctk.CTkToplevel(self.root)
        SweepIV_Window(new_window)
    
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
            
            self.ax.set_title('')
            self.ax.set_xlabel('Bias Voltage (V)')
            self.ax.set_ylabel('Current (A)')
        except FileNotFoundError:
            pass
