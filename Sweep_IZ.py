from tkinter import *
from tkinter import messagebox
from PIL import Image
import customtkinter as ctk

class SweepIZ_Window:
    def __init__(self, root):
        self.root = root
        self.root.title("Piezo Sweep Parameters")
        self.root.config(bg="#d3d3d3")
        self.root.geometry("475x175")
        
        # Initialize the widgets
        self.init_iz_sweep_widgets()
    
    def init_iz_sweep_widgets(self):
        # min voltage
        self.frame1 = LabelFrame(self.root, text="Minimum Voltage (V)", padx=10, pady=2, bg="#708090")
        self.label1 = Entry(self.frame1, bg="white", width=25)
        
        # max voltage
        self.frame2 = LabelFrame(self.root, text="Maximum Voltage (V)", padx=10, pady=2, bg="#708090")
        self.label2 = Entry(self.frame2, bg="white", width=25)
        
        # save button
        self.add_btn_image1 = ctk.CTkImage(Image.open("Images/Save_Btn.png"), size=(50,14))
        self.add_btn_image2 = ctk.CTkImage(Image.open("Images/Exit_Btn.png"), size=(50,14))
        
        # exit button
        self.save_btn = ctk.CTkButton(self.root, image=self.add_btn_image1, text="", width=50, height=14, fg_color="#d3d3d3", bg_color="#d3d3d3", corner_radius=0)
        self.exit_btn = ctk.CTkButton(self.root, image=self.add_btn_image2, text="", width=50, height=14, fg_color="#d3d3d3", bg_color="#d3d3d3", corner_radius=0)
        
        self.publish_iz_sweep_widgets()
        
    def publish_iz_sweep_widgets(self):
        # start voltage
        self.frame1.grid(row=2, column=2, padx=50, pady=50)
        self.label1.grid(row=0, column=0, padx=5, pady=5)
        
        # stop voltage
        self.frame2.grid(row=2, column=3, padx=5, pady=5)
        self.label2.grid(row=0, column=0, padx=5, pady=5)
        
        # buttons
        self.save_btn.grid(row=3, column=5, padx=5, sticky="se")
        self.exit_btn.grid(row=4, column=5, padx=5, sticky="ne")   