from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import threading
from PIL import Image, ImageTk
import PIL
import customtkinter

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class RootGUI:
    def __init__(self):
        self.root = customtkinter.CTk()
        self.root.title("Homepage")
        self.root.config(bg="skyblue")
        self.root.geometry("1000x650")
        
    def close_window(self):
        print("Closing window and exiting") # debug, delete later 
        self.root.destroy()

# class for measurements/text box widgets in homepage
class MeasGUI():
    def __init__(self,root):
        self.root = root
        
        # current distance
        self.frame1 = LabelFrame(root, text = "Distance (nm)", 
                                padx=10, pady=2, bg="gray")
        self.label1 = Entry(self.frame1, bg="white", width=25)
        
        # current
        self.frame2 = LabelFrame(root, text = "Current (nA)", 
                                padx=10, pady=2, bg="gray")
        self.label2 = Entry(self.frame2, bg="white", width=25)
        
        # critical distance
        self.frame3 = LabelFrame(root, text="Critical Distance (nm)", 
                                 padx=10, pady=2, bg="gray")
        self.label3 = Entry(self.frame3, bg="white", width=25)
        
        # critical current
        self.frame4 = LabelFrame(root, text="Critical Current (nA)", 
                                 padx=10, pady=2, bg="gray")
        self.label4 = Entry(self.frame4, bg="white", width=25)
        
        # current setpoint
        self.frame5 = LabelFrame(root, text="Current Setpoint (nA)", 
                                 padx=10, pady=2, bg="gray")
        self.label5 = Entry(self.frame5, bg="white", width=25)
        
        # current offset
        self.frame6 = LabelFrame(root, text="Current Offset (nA)", 
                                 padx=10, pady=2, bg="gray")
        self.label6 = Entry(self.frame6, bg="white", width=25)
        
        # user notes text box
        self.frame7 = LabelFrame(root, text="NOTES",
                                 padx=10, pady=5, bg="gray")
        self.label7 = Text(self.frame7, height=5, width=30)
        self.label8 = Text(self.frame7, height=1, width=5)
        self.label9 = Label(self.frame7, text="Date:", height=1, width=5)
        
        # setup the drop option menu
        self.DropDownMenu()
        
        # optional graphic parameters
        self.padx=20
        self.pady=10
        
        # put on the grid all the elements
        self.publish()
    
    def publish(self):
        self.frame1.grid(row=1, column=2, padx=5, pady=5)
        self.label1.grid(row=5, column=1)
        
        self.frame2.grid(row=2, column=2, padx=5, pady=5)
        self.label2.grid(row=2, column=1)   
        
        self.frame3.grid(row=1, column=3, padx=5, pady=5)
        self.label3.grid(row=2, column=1) 
        
        self.frame4.grid(row=2, column=3, padx=5, pady=5)
        self.label4.grid(row=2, column=1) 
        
        self.frame5.grid(row=3, column=2, padx=5, pady=5)
        self.label5.grid(row=2, column=1) 
        
        self.frame6.grid(row=3, column=3, padx=5, pady=5)
        self.label6.grid(row=2, column=1) 
        
        self.frame7.grid(row=13, column=7, padx=5, pady=5)
        self.label7.grid(row=13, column=1) 
        self.label8.grid(row=1, column=2, pady=5)
        self.label9.grid(row=1, column=1, pady=5, sticky="e")
        
        # file drop-down menu
        self.drop_menu.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        self.drop_menu.grid(row=0, column=0, padx=self.padx)
        
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
class GraphGUI():
    def __init__(self, root):
        self.root = root
        #self.serial = serial
        #self.data = data
        self.fig = []
        
        #def AddGraph(self):

# class for creating buttons
class ButtonGUI():
    def __init__(self, root):
        self.root = root
        
        # define images
        self.add_btn_image1 = ImageTk.PhotoImage(Image.open("Images/Retract_Tip_Btn.png"))
        self.add_btn_image2 = ImageTk.PhotoImage(Image.open("Images/Fine_Adjust_Btn_Up.png"))
        self.add_btn_image3 = ImageTk.PhotoImage(Image.open("Images/Fine_Adjust_Btn_Down.png"))
        self.add_btn_image4 = ImageTk.PhotoImage(Image.open("Images/Start_Btn.png"))
        self.add_btn_image5 = ImageTk.PhotoImage(Image.open("Images/Stop_Btn.png"))
        self.add_btn_image6 = ImageTk.PhotoImage(Image.open("Images/Acquire_IV.png"))
        self.add_btn_image7 = ImageTk.PhotoImage(Image.open("Images/Acquire_IZ.png"))
        self.add_btn_image8 = ImageTk.PhotoImage(Image.open("Images/Stop_LED.png"))
        
        # create buttons
        self.retract_tip_btn = customtkinter.CTkButton(master=root, image=self.add_btn_image1, text="", compound="bottom", width=20, height=40, fg_color="skyblue", bg_color="skyblue", corner_radius=0)
        self.fine_adjust_btn_up = customtkinter.CTkButton(master=root, image=self.add_btn_image2, text="", compound="bottom", width=20, height=20, fg_color="skyblue", bg_color="skyblue", corner_radius=0)
        self.fine_adjust_btn_down = customtkinter.CTkButton(master=root, image=self.add_btn_image3, text="", compound="bottom", width=20, height=20, fg_color="skyblue", bg_color="skyblue", corner_radius=0)
        self.start_btn = customtkinter.CTkButton(master=root, image=self.add_btn_image4, text="", compound="bottom", width=20, height=20, fg_color="skyblue", bg_color="skyblue", corner_radius=0)
        self.stop_btn = customtkinter.CTkButton(master=root, image=self.add_btn_image5, text="", compound="bottom", width=20, height=20, fg_color="skyblue", bg_color="skyblue", corner_radius=0)
        self.acquire_iv_btn = customtkinter.CTkButton(master=root, image=self.add_btn_image6, text="", compound="bottom", width=20, height=20, fg_color="skyblue", bg_color="skyblue", corner_radius=0)
        self.acquire_iz_btn = customtkinter.CTkButton(master=root, image=self.add_btn_image7, text="", compound="bottom", width=20, height=20, fg_color="skyblue", bg_color="skyblue", corner_radius=0)
        self.stop_led_btn = customtkinter.CTkButton(master=root, image=self.add_btn_image8, text="", compound="bottom", width=15, height=40, fg_color="skyblue", bg_color="skyblue", corner_radius=0)
        
        self.DisplayGUI()
        
    def DisplayGUI(self):
        '''
        Method to display all button widgets
        '''
        self.retract_tip_btn.grid(column=1, row=10, padx=5, pady=5)
        self.fine_adjust_btn_up.grid(column=2, row=10, padx=5, pady=5)
        self.fine_adjust_btn_down.grid(column=2, row=11, padx=5, pady=5)
        self.start_btn.grid(column=9, row=1, padx=5, pady=5)
        self.stop_btn.grid(column=9, row=2, padx=5, pady=5)
        self.acquire_iv_btn.grid(column=9, row=3, padx=5, pady=5)
        self.acquire_iz_btn.grid(column=9, row=4, padx=5, pady=5)
        self.stop_led_btn.grid(column=10, row=1, padx=5, pady=5)
        
                     
if __name__ == "__main__":
    RootGUI()
    MeasGUI()
    GraphGUI()
    ButtonGUI()
