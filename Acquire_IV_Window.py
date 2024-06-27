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

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import time

class RootGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Acquire I-V")
        self.root.config(bg="#ADD8E6")
        self.root.geometry("1100x650")
        
        # Add a method to quit the application
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
        
    def quit_application(self):
        print("Quitting application")
        self.root.quit()

# class for measurements/text box widgets in homepage
class MeasGUI:
    def __init__(self, root):
        self.root = root
        
        # current
        self.frame1 = LabelFrame(root, text="Current (nm)", padx=10, pady=2, bg="gray")
        self.label1 = Entry(self.frame1, bg="white", width=25)
        
        # critical current
        self.frame2 = LabelFrame(root, text="Critical Current (nA)", padx=10, pady=2, bg="gray")
        self.label2 = Entry(self.frame2, bg="white", width=25)

        # sample bias voltage
        self.frame3 = LabelFrame(root, text="Sample Bias Voltage (V)", padx=10, pady=2, bg="gray")
        self.label3 = Entry(self.frame3, bg="white", width=25)
        
        # critical bias voltage
        self.frame4 = LabelFrame(root, text="Critical Bias Voltage (V)", padx=10, pady=2, bg="gray")
        self.label4 = Entry(self.frame4, bg="white", width=25)
        
        # sample rate
        self.frame5 = LabelFrame(root, text="Sample Rate", padx=10, pady=2, bg="#7393B3")
        self.label5 = Entry(self.frame5, bg="white", width=25)
        
        # TEST FOR BOUNDARIES
        #self.frame6 = LabelFrame(root, text="TEST BOUNDARIES", padx=10, pady=2, bg="#7393B3")
        #self.label6 = Entry(self.frame6, bg="white", width=25)
        
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
        # current
        self.frame1.grid(row=1, column=10, padx=5, pady=5)
        self.label1.grid(row=0, column=0, padx=5, pady=5)
        
        # critical current
        self.frame2.grid(row=1, column=11, padx=5, pady=5)
        self.label2.grid(row=0, column=0, padx=5, pady=5)   
        
        # sample bias voltage
        self.frame3.grid(row=2, column=10, padx=5, pady=5)
        self.label3.grid(row=0, column=0, padx=5, pady=5) 
        
        # critical bias voltage
        self.frame4.grid(row=2, column=11, padx=5, pady=5)
        self.label4.grid(row=0, column=0, padx=5, pady=5) 
        
        # sample rate
        self.frame5.grid(row=3, column=10, padx=5, pady=5)
        self.label5.grid(row=0, column=0, padx=5, pady=5) 
        
        # TEST FOR BOUNDARIES
        #self.frame6.grid(row=10, column=11, padx=5, pady=5)
        #self.label6.grid(row=0, column=0, padx=5, pady=5) 
        
        # Positioning the notes section
        self.frame7.grid(row=10, column=9, rowspan=4, columnspan=2, padx=5, pady=5)
        self.label7.grid(row=1, column=0, padx=5, pady=5) 
        self.label8.grid(row=0, column=2, pady=5)
        self.label9.grid(row=0, column=1, pady=5, sticky="e")
        
        # Positioning the file drop-down menu
        self.drop_menu.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        
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

#DATA_FILE_PATH = 'fakedata.txt'

#style.use('ggplot')

#fig = plt.figure()
#graph = fig.add_subplot(1,1,1)

# class for graph in homepage
class GraphGUI:
    def __init__(self, root):
        self.root = root
        self.create_graph()
        #self.animate()
        
    def create_graph(self):
        # Create a figure
        self.fig, self.graph = plt.subplots()
        self.graph.set_xlabel('Time (s)')
        self.graph.set_ylabel('Tunneling Current (nA)')
        self.fig.set_figwidth(8)
        self.fig.set_figheight(5.5)
        
        # Create a canvas to embed the figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=1, column=0, columnspan=10, rowspan=8, padx=10, pady=10)

#getting crazy

    #def animate(self):
    #    graph_data = open(DATA_FILE_PATH, 'r').read()
    #    lines = graph_data.split('\n')
    #    xdata = []
    #    ydata = []
    #    for line in lines:
    #        if len(line) > 1:
    #            x, y = line.split(',')
    #            xdata.append(float(x))
    #            ydata.append(float(y))
    #    graph.clear()
    #    graph.plot(xdata,ydata, c='#64B9FF')
    #    
    #    plt.title('Sample Data Live Graph')
    #    plt.xlabel('X Sample Label')
    #    plt.ylabel('Y Sample Label')
    



# NOT CURRENTLY USING
# class for creating buttons
class ButtonGUI:
    def __init__(self, root):
        self.root = root
        
        # define images
        #self.add_btn_image1 = ctk.CTkImage(Image.open("Images/Retract_Tip_Btn.png"), size=(40,80))
        #self.add_btn_image2 = ctk.CTkImage(Image.open("Images/Fine_Adjust_Btn_Up.png"), size=(40,40))
        #self.add_btn_image3 = ctk.CTkImage(Image.open("Images/Fine_Adjust_Btn_Down.png"), size=(40,40))
        self.add_btn_image4 = ctk.CTkImage(Image.open("Images/Start_Btn.png"), size=(90,35))
        self.add_btn_image5 = ctk.CTkImage(Image.open("Images/Stop_Btn.png"), size=(90,35))
        #self.add_btn_image6 = ctk.CTkImage(Image.open("Images/Acquire_IV.png"), size=(90,35))
        #self.add_btn_image7 = ctk.CTkImage(Image.open("Images/Acquire_IZ.png"), size=(90,35))
        self.add_btn_image8 = ctk.CTkImage(Image.open("Images/Stop_LED.png"), size=(35,35))
        self.add_btn_image1 = ctk.CTkImage(Image.open("Images/Sample_Bias_Sweep_Parameters.png"), size=(90,35))
        self.add_btn_image2 = ctk.CTkImage(Image.open("Images/Homepage.png"), size=(90,35))

        
        # create buttons with proper sizes
        #self.retract_tip_btn = ctk.CTkButton(master=root, image=self.add_btn_image1, text_color="black", width=40, height=80, text="Retract Tip", compound="bottom", fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        #self.fine_adjust_btn_up = ctk.CTkButton(master=root, image=self.add_btn_image2, text_color="black", width=40, height=40, text="Fine Adjustment", compound="bottom", fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        #self.fine_adjust_btn_down = ctk.CTkButton(master=root, image=self.add_btn_image3, text="", compound="bottom", width=40, height=40, fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        self.start_btn = ctk.CTkButton(master=root, image=self.add_btn_image4, text="", width=90, height=35, fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        self.stop_btn = ctk.CTkButton(master=root, image=self.add_btn_image5, text="", width=90, height=35, fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        #self.acquire_iv_btn = ctk.CTkButton(master=root, image=self.add_btn_image6, text="", width=90, height=35, fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        #self.acquire_iz_btn = ctk.CTkButton(master=root, image=self.add_btn_image7, text="", width=90, height=35, fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        self.stop_led_btn = ctk.CTkButton(master=root, image=self.add_btn_image8, text="", width=30, height=35, fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        self.homepage_btn = ctk.CTkButton(master=root, image=self.add_btn_image2, text="", width=90, height=35, fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)
        self.sample_bias_sweep_parameters_btn = ctk.CTkButton(master=root, image=self.add_btn_image1, text="", width=90, height=35, fg_color="#ADD8E6", bg_color="#ADD8E6", corner_radius=0)

        self.DisplayGUI()
        
    def DisplayGUI(self):
        '''
        Method to display all button widgets
        '''
        #self.retract_tip_btn.grid(row=10, column=0, rowspan=2)
        #self.fine_adjust_btn_up.grid(row=10, column=1)
        #self.fine_adjust_btn_down.grid(row=11, column=1)
        self.start_btn.grid(row=10, column=0, sticky="e")
        self.stop_btn.grid(row=11, column=0, sticky="e")
        #self.acquire_iv_btn.grid(row=3, column=5, sticky="e")
        #self.acquire_iz_btn.grid(row=4, column=5, sticky="e")
        self.stop_led_btn.grid(row=10, column=1)
        self.homepage_btn.grid(row=10, column=12)
        self.sample_bias_sweep_parameters_btn.grid(row=11, column=12, sticky="")

if __name__ == "__main__":
    root_gui = RootGUI()
    MeasGUI(root_gui.root)
    GraphGUI(root_gui.root)
    #ani = animation.FuncAnimation(fig, animate, interval=1000, cache_frame_data=False)
    

    #plt.show()
    ButtonGUI(root_gui.root) #dont have button images yet
    root_gui.root.mainloop()
    