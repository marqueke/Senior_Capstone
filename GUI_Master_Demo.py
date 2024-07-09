<<<<<<< Updated upstream
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import threading
from PIL import Image, ImageTk
import PIL
import customtkinter as ctk
import tkinter as tk
import serial
import serial.tools.list_ports

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from IV_Window import IVWindow  # import the IV Window Class
from IZ_Window import IZWindow  # import the IV Window Class
from SPI_Data_Ctrl import SerialCtrl
from value_conversion import Convert

# NOTE: ADD drop down list for sample rates

class RootGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Homepage")
        self.root.config(bg="#eeeeee")
        self.root.geometry("1100x650")
        
        # Add a method to quit the application
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
        
    def quit_application(self):
        print("Quitting application")
        #self.serial_controller.stop()
        self.root.quit()
    

# Class to setup and create the communication manager with MCU
class ComGUI():
    def __init__(self, root, serial):
        '''
        Initialize the connexion GUI and initialize the main widgets 
        '''
        # Initializing the Widgets
        self.root = root
        self.serial = serial
        self.frame = LabelFrame(root, text="Com Manager",
                                padx=5, pady=5, bg="white")
        self.label_com = Label(
            self.frame, text="Available Port(s): ", bg="white", width=15, anchor="w")

        # Setup the Drop option menu
        self.ComOptionMenu()

        # Add the control buttons for refreshing the COMs & Connect
        self.btn_refresh = Button(self.frame, text="Refresh",
                                  width=10,  command=self.com_refresh)
        self.btn_connect = Button(self.frame, text="Connect",
                                  width=10, state="disabled",  command=self.serial_connect)

        # Optional Graphic parameters
        self.padx = 7
        self.pady = 5

        # Put on the grid all the elements
        self.publish()

    def publish(self):
        '''
         Method to display all the Widget of the main frame
        '''
        self.frame.grid(row=1, column=0, rowspan=3,
                        columnspan=3, padx=5, pady=5)
        self.label_com.grid(column=1, row=2)

        self.drop_com.grid(column=2, row=2, padx=self.padx)

        self.btn_refresh.grid(column=3, row=2, padx=self.padx)
        self.btn_connect.grid(column=3, row=3, padx=self.padx)

    def ComOptionMenu(self):
        '''
         Method to Get the available COMs connected to the PC
         and list them into the drop menu
        '''
        # Generate the list of available coms

        self.serial.getCOMList()

        self.clicked_com = StringVar()
        self.clicked_com.set(self.serial.com_list[0])
        self.drop_com = OptionMenu(
            self.frame, self.clicked_com, *self.serial.com_list, command=self.connect_ctrl)

        self.drop_com.config(width=10)

    def connect_ctrl(self, widget):
        '''
        Mehtod to keep the connect button disabled if all the 
        conditions are not cleared
        '''
        print("Connect ctrl")
        # Checking the logic consistency to keep the connection btn
        if "-" in self.clicked_com.get():         
            self.btn_connect["state"] = "disabled"
        else:
            self.btn_connect["state"] = "active"

    def com_refresh(self):
        print("Refresh")
        # Get the Widget destroyed
        self.drop_com.destroy()

        # Refresh the list of available Coms
        self.ComOptionMenu()

        # Publish the this new droplet
        self.drop_com.grid(column=2, row=2, padx=self.padx)

        # Just in case to secure the connect logic
        logic = []
        self.connect_ctrl(logic)

    def serial_connect(self):
        '''
        Method that Updates the GUI during connect / disconnect status
        Manage serials and data flows during connect / disconnect status
        '''
        if self.btn_connect["text"] in "Connect":
            # Start the serial communication
            self.serial.SerialOpen(self)

            # If connection established move on
            if self.serial.ser.status:
                # Update the COM manager
                self.btn_connect["text"] = "Disconnect"
                self.btn_refresh["state"] = "disable"
                self.drop_com["state"] = "disable"
                InfoMsg = f"Successful UART connection using {self.clicked_com.get()}"
                messagebox.showinfo("showinfo", InfoMsg)

            else:
                ErrorMsg = f"Failure to estabish UART connection using {self.clicked_com.get()} "
                messagebox.showerror("showerror", ErrorMsg)
        else:

            # Closing the Serial COM
            # Close the serial communication
            self.serial.SerialClose(self)

            InfoMsg = f"UART connection using {self.clicked_com.get()} is now closed"
            messagebox.showwarning("showinfo", InfoMsg)
            self.btn_connect["text"] = "Connect"
            self.btn_refresh["state"] = "active"
            self.drop_com["state"] = "active"
    
# class for measurements/text box widgets in homepage
class MeasGUI:
    def __init__(self, root):
        self.root = root
        
        # current distance
        self.frame1 = LabelFrame(root, text="Distance (nm)", padx=10, pady=2, bg="gray")
        self.label1 = Entry(self.frame1, bg="white", width=20)
        
        # current
        self.frame2 = LabelFrame(root, text="Critical Distance (nm)", padx=10, pady=2, bg="gray")
        self.label2 = Entry(self.frame2, bg="white", width=20)
        
        # critical distance
        self.frame3 = LabelFrame(root, text="Current (nA)", padx=10, pady=2, bg="gray")
        self.label3 = Entry(self.frame3, bg="white", width=20)
        
        # critical current
        self.frame4 = LabelFrame(root, text="Critical Current (nA)", padx=10, pady=2, bg="gray")
        self.label4 = Entry(self.frame4, bg="white", width=20)
        
        # current setpoint
        self.frame5 = LabelFrame(root, text="Current Setpoint (nA)", padx=10, pady=2, bg="#ADD8E6")
        self.label5 = Entry(self.frame5, bg="white", width=20)
        
        # current offset
        self.frame6 = LabelFrame(root, text="Current Offset (nA)", padx=10, pady=2, bg="#ADD8E6")
        self.label6 = Entry(self.frame6, bg="white", width=20)
        
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
        
        # put on the grid all the elements
        self.publish()
    
    def publish(self):
        self.frame1.grid(row=11, column=4, padx=5, pady=5, sticky="sw")
        self.label1.grid(row=0, column=0, padx=5, pady=5)
        
        self.frame2.grid(row=11, column=5, padx=5, pady=5, sticky="sw")
        self.label2.grid(row=0, column=1, padx=5, pady=5)   
        
        self.frame3.grid(row=12, column=4, padx=5, pady=5, sticky="w")
        self.label3.grid(row=1, column=0, padx=5, pady=5) 
        
        self.frame4.grid(row=12, column=5, padx=5, pady=5, sticky="w")
        self.label4.grid(row=1, column=1, padx=5, pady=5) 
        
        self.frame5.grid(row=13, column=4, padx=5, pady=5, sticky="nw")
        self.label5.grid(row=2, column=0, padx=5, pady=5) 
        
        self.frame6.grid(row=13, column=5, padx=5, pady=5, sticky="nw")
        self.label6.grid(row=2, column=1, padx=5, pady=5) 
        
        # Positioning the notes section
        self.frame7.grid(row=11, column=7, rowspan=3, pady=5, sticky="n")
        self.label7.grid(row=1, column=0, pady=5, columnspan=3, rowspan=3) 
        self.label8.grid(row=0, column=2, pady=5, sticky="e")
        self.label9.grid(row=0, column=2, pady=5, sticky="w")
        
        # Positioning the file drop-down menu
        self.drop_menu.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
    def update_distance(self, data):
        self.label1.delete(0, END)
        self.label1.insert(0, data)
             
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
        self.drop_menu = OptionMenu(self.root, self.menu_options, *options)
        self.drop_menu.config(width=10)

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

# class for creating buttons
class ButtonGUI:
    def __init__(self, root):
        self.root = root
        
        # define images
        self.add_btn_image1 = ctk.CTkImage(Image.open("Images/Retract_Tip_Btn.png"), size=(40,80))
        self.add_btn_image2 = ctk.CTkImage(Image.open("Images/Fine_Adjust_Btn_Up.png"), size=(40,40))
        self.add_btn_image3 = ctk.CTkImage(Image.open("Images/Fine_Adjust_Btn_Down.png"), size=(40,40))
        self.add_btn_image4 = ctk.CTkImage(Image.open("Images/Start_Btn.png"), size=(90,35))
        self.add_btn_image5 = ctk.CTkImage(Image.open("Images/Stop_Btn.png"), size=(90,35))
        self.add_btn_image6 = ctk.CTkImage(Image.open("Images/Acquire_IV.png"), size=(90,35))
        self.add_btn_image7 = ctk.CTkImage(Image.open("Images/Acquire_IZ.png"), size=(90,35))
        self.add_btn_image8 = ctk.CTkImage(Image.open("Images/Stop_LED.png"), size=(35,35))
        
        # create buttons with proper sizes
        self.start_btn = ctk.CTkButton(master=root, image=self.add_btn_image4, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0)
        self.stop_btn = ctk.CTkButton(master=root, image=self.add_btn_image5, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0)
        self.acquire_iv_btn = ctk.CTkButton(master=root, image=self.add_btn_image6, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.open_iv_window)
        self.acquire_iz_btn = ctk.CTkButton(master=root, image=self.add_btn_image7, text="", width=90, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0, command=self.open_iz_window)
        self.stop_led_btn = ctk.CTkButton(master=root, image=self.add_btn_image8, text="", width=30, height=35, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0)
        
        self.retract_tip_frame = LabelFrame(root, text="Retract Tip", padx=10, pady=5, bg="#eeeeee")
        self.retract_tip_btn = ctk.CTkButton(master=self.retract_tip_frame, image=self.add_btn_image1, width=40, height=100, text="", compound="bottom", fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0)
        
        self.fine_adjust_frame = LabelFrame(root, text="Fine Adjust", padx=10, pady=5, bg="#eeeeee")
        self.fine_adjust_btn_up = ctk.CTkButton(master=self.fine_adjust_frame, image=self.add_btn_image2, text = "", width=40, height=40, compound="bottom", fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0)
        self.fine_adjust_btn_down = ctk.CTkButton(master=self.fine_adjust_frame, image=self.add_btn_image3, text="", compound="bottom", width=40, height=40, fg_color="#eeeeee", bg_color="#eeeeee", corner_radius=0)
        
        self.vbias_frame = LabelFrame(root, text="Vbias", padx=10, pady=2, bg="#7393B3")
        self.vbias_label = Entry(self.vbias_frame, bg="white", width=15)
        
        self.DisplayGUI()
        
    def DisplayGUI(self):
        '''
        Method to display all button widgets
        '''
        self.retract_tip_frame.grid(row=11, column=0, rowspan=3, columnspan=2, padx=20, sticky="e")
        self.retract_tip_btn.grid(row=11, column=0)
        
        self.fine_adjust_frame.grid(row=11, column=1, rowspan=3, columnspan=2, padx=5, sticky="e")
        self.fine_adjust_btn_up.grid(row=11, column=0)
        self.fine_adjust_btn_down.grid(row=12, column=0)
        
        self.start_btn.grid(row=2, column=9, sticky="e")
        self.stop_btn.grid(row=3, column=9, sticky="ne")
        self.acquire_iv_btn.grid(row=4, column=9, sticky="ne")
        self.acquire_iz_btn.grid(row=5, column=9, sticky="ne")
        self.stop_led_btn.grid(row=2, column=10, sticky="e")

        self.vbias_frame.grid(row=6, column=9, padx=5, pady=5, sticky="ne")
        self.vbias_label.grid(row=6, column=9, padx=5, pady=5)
        
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
    
    

if __name__ == "__main__":
    RootGUI()
    MeasGUI()
