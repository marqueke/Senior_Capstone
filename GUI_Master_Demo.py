from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import threading
from PIL import Image, ImageTk
import PIL
import customtkinter as ctk
import tkinter as tk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class RootGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Homepage")
        self.root.config(bg="#ADD8E6")
        self.root.geometry("1100x650")
        
        # Add a method to quit the application
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
        
    def quit_application(self):
        print("Quitting application")
        self.root.quit()

# class to setup and create the communication manager with the MCU
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
        self.label_bd = Label(
            self.frame, text="Baude Rate: ", bg="white", width=15, anchor="w")

        # Setup the Drop option menu
        self.baudOptionMenu()
        self.ComOptionMenu()

        # Add the control buttons for refreshing the COMs & Connect
        self.btn_refresh = Button(self.frame, text="Refresh",
                                  width=10,  command=self.com_refresh)
        self.btn_connect = Button(self.frame, text="Connect",
                                  width=10, state="disabled",  command=self.serial_connect)

        # Optional Graphic parameters
        self.padx = 20
        self.pady = 5

        # Put on the grid all the elements
        self.publish()

    def publish(self):
        '''
         Method to display all the Widget of the main frame
        '''
        self.frame.grid(row=0, column=0, rowspan=3,
                        columnspan=3, padx=5, pady=5)
        self.label_com.grid(column=0, row=2)
        self.label_bd.grid(column=0, row=3)

        self.drop_baud.grid(column=1, row=3, padx=self.padx, pady=self.pady)
        self.drop_com.grid(column=1, row=2, padx=self.padx)

        self.btn_refresh.grid(column=2, row=2)
        self.btn_connect.grid(column=2, row=3)

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

    def baudOptionMenu(self):
        '''
         Method to list all the baud rates in a drop menu
        '''
        self.clicked_bd = StringVar()
        bds = ["-",
               "300",
               "600",
               "1200",
               "2400",
               "4800",
               "9600",
               "14400",
               "19200",
               "28800",
               "38400",
               "56000",
               "57600",
               "115200",
               "128000",
               "256000"]
        self.clicked_bd .set(bds[0])
        self.drop_baud = OptionMenu(
            self.frame, self.clicked_bd, *bds, command=self.connect_ctrl)
        self.drop_baud.config(width=10)

    def connect_ctrl(self, widget):
        '''
        Mehtod to keep the connect button disabled if all the 
        conditions are not cleared
        '''
        print("Connect ctrl")
        
        if "-" in self.clicked_com.get() or "-" in self.clicked_bd.get():
            self.btn_connect["state"] = "disable"
        else:
            self.btn_connect["state"] = "active"

    def com_refresh(self):
        self.drop_com.destroy()
        self.ComOptionMenu()
        self.drop_com.grid(column=1, row=2, padx=self.padx)
        logic = []
        self.connect_ctrl(logic)
        

    def serial_connect(self):
        if self.btn_connect["text"] in "Connect":
            self.serial.SerialOpen(self)
            if self.serial.ser.status:
                self.btn_connect["text"] = "Disconnect"
                self.btn_refresh["text"] = "disable"
                self.drop_baud["state"] = "disable"
                self.drop_com["state"] = "disable"
                InfoMsg = f"Successful UART connection using {self.clicked_com.get()}."
                messagebox.showinfo("Success", InfoMsg)
            else:
                ErrorMsg = f"Failure to establish UART connection using {self.clicked_com.get()}."
                messagebox.showerror("Error", ErrorMsg)
        else:
            # closing serial COM
            # close sesrial communication
            self.serial.SerialClose(self)
            
            InfoMsg = f"UART connection using {self.clicked_com.get()} is now closed."
            messagebox.showwarning("Warning", InfoMsg)
            self.btn_connect["text"] = "Connect"
            self.btn_refresh["state"] = "active"
            self.drop_baud["state"] = "active"
            self.drop_com["state"] = "active"
    
# class for measurements/text box widgets in homepage
class MeasGUI:
    def __init__(self, root):
        self.root = root
        
        # current distance
        self.frame1 = LabelFrame(root, text="Distance (nm)", padx=10, pady=2, bg="gray")
        self.label1 = Entry(self.frame1, bg="white", width=25)
        
        # current
        self.frame2 = LabelFrame(root, text="Critical Distance (nm)", padx=10, pady=2, bg="gray")
        self.label2 = Entry(self.frame2, bg="white", width=25)
        
        # critical distance
        self.frame3 = LabelFrame(root, text="Current (nA)", padx=10, pady=2, bg="gray")
        self.label3 = Entry(self.frame3, bg="white", width=25)
        
        # critical current
        self.frame4 = LabelFrame(root, text="Critical Current (nA)", padx=10, pady=2, bg="gray")
        self.label4 = Entry(self.frame4, bg="white", width=25)
        
        # current setpoint
        self.frame5 = LabelFrame(root, text="Current Setpoint (nA)", padx=10, pady=2, bg="#7393B3")
        self.label5 = Entry(self.frame5, bg="white", width=25)
        
        # current offset
        self.frame6 = LabelFrame(root, text="Current Offset (nA)", padx=10, pady=2, bg="#7393B3")
        self.label6 = Entry(self.frame6, bg="white", width=25)
        
        # user notes text box
        self.frame7 = LabelFrame(root, text="NOTES", padx=10, pady=5, bg="gray")
        self.label7 = Text(self.frame7, height=5, width=30)
        self.label8 = Text(self.frame7, height=1, width=5)
        self.label9 = Label(self.frame7, text="Date:", height=1, width=5)
        
        # setup the drop option menu
        self.DropDownMenu()
        
        # optional graphic parameters
        self.padx = 20
        self.pady = 10
        
        # put on the grid all the elements
        self.publish()
    
    def publish(self):
        self.frame1.grid(row=5, column=2, padx=5, pady=20, sticky="nw")
        self.label1.grid(row=0, column=0, padx=5, pady=5, rowspan=2)
        
        self.frame2.grid(row=5, column=2, padx=5, pady=20, sticky="sw")
        self.label2.grid(row=0, column=0, padx=5, pady=5)   
        
        self.frame3.grid(row=5, column=3, padx=5, pady=20, sticky="sw")
        self.label3.grid(row=0, column=0, padx=5, pady=5) 
        
        self.frame4.grid(row=5, column=3, padx=5, pady=20, sticky="nw")
        self.label4.grid(row=0, column=0, padx=5, pady=5, rowspan=2) 
        
        self.frame5.grid(row=5, column=4, padx=5, pady=20, sticky="nw")
        self.label5.grid(row=0, column=0, padx=5, pady=5, rowspan=2) 
        
        self.frame6.grid(row=5, column=4, padx=5, pady=20, sticky="sw")
        self.label6.grid(row=0, column=0, padx=5, pady=5) 
        
        # Positioning the notes section
        self.frame7.grid(row=6, column=5, rowspan=2, padx=5, pady=5)
        self.label7.grid(row=1, column=0, padx=5, pady=5) 
        self.label8.grid(row=0, column=2, pady=5)
        self.label9.grid(row=0, column=1, pady=5, sticky="e")
        
        # Positioning the file drop-down menu
        self.drop_menu.grid(row=0, column=0, padx=5, pady=5)
        
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
        self.canvas.get_tk_widget().grid(row=0, column=2, columnspan=6, rowspan=5, padx=10, pady=5)

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
        self.start_btn = ctk.CTkButton(master=root, image=self.add_btn_image4, text="", width=90, height=35, fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        self.stop_btn = ctk.CTkButton(master=root, image=self.add_btn_image5, text="", width=90, height=35, fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        self.acquire_iv_btn = ctk.CTkButton(master=root, image=self.add_btn_image6, text="", width=90, height=35, fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0, command=self.open_iv_window)
        self.acquire_iz_btn = ctk.CTkButton(master=root, image=self.add_btn_image7, text="", width=90, height=35, fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0, command=self.open_iz_window)
        self.stop_led_btn = ctk.CTkButton(master=root, image=self.add_btn_image8, text="", width=30, height=35, fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        
        self.retract_tip_frame = LabelFrame(root, text="Retract Tip", padx=10, pady=5, bg="#ADD8E6")
        self.retract_tip_btn = ctk.CTkButton(master=self.retract_tip_frame, image=self.add_btn_image1, width=40, height=100, text="", compound="bottom", fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        
        self.fine_adjust_frame = LabelFrame(root, text="Fine Adjust", padx=10, pady=5, bg="#ADD8E6")
        self.fine_adjust_btn_up = ctk.CTkButton(master=self.fine_adjust_frame, image=self.add_btn_image2, text = "", width=40, height=40, compound="bottom", fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        self.fine_adjust_btn_down = ctk.CTkButton(master=self.fine_adjust_frame, image=self.add_btn_image3, text="", compound="bottom", width=40, height=40, fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        
        self.DisplayGUI()
        
    def DisplayGUI(self):
        '''
        Method to display all button widgets
        '''
        self.retract_tip_frame.grid(row=5, column=0)
        self.retract_tip_btn.grid(row=5, column=0, rowspan=2)
        
        self.fine_adjust_frame.grid(row=5, column=1)
        self.fine_adjust_btn_up.grid(row=5, column=1)
        self.fine_adjust_btn_down.grid(row=6, column=1)
        
        self.start_btn.grid(row=1, column=5, sticky="e")
        self.stop_btn.grid(row=2, column=5, sticky="ne")
        self.acquire_iv_btn.grid(row=3, column=5, sticky="ne")
        self.acquire_iz_btn.grid(row=4, column=5, sticky="ne")
        self.stop_led_btn.grid(row=1, column=6, sticky="e")

    def open_iv_window(self):
        '''
        Method to open a new window when the "Acquire I-V" button is clicked
        '''
        new_window = ctk.CTkToplevel(self.root)
        new_window.title("I-V Acquisition")
        new_window.geometry("1000x600")
        label = ctk.CTkLabel(new_window, text="I-V Acquisition Data")
        label.pack(padx=20, pady=20)

    def open_iz_window(self):
        '''
        Method to open a new window when the "Acquire I-Z" button is clicked
        '''
        new_window = ctk.CTkToplevel(self.root)
        new_window.title("I-Z Acquisition")
        new_window.geometry("1000x600")
        label = ctk.CTkLabel(new_window, text="I-Z Acquisition Data")
        label.pack(padx=20, pady=20)

if __name__ == "__main__":
    root_gui = RootGUI()
    MeasGUI(root_gui.root)
    GraphGUI(root_gui.root)
    ButtonGUI(root_gui.root)
    ComGUI(root_gui.root)
    root_gui.root.mainloop()
