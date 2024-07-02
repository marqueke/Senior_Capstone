# iv_window.py

from tkinter import *
from tkinter import messagebox
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation

class IVWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Acquire I-V")
        self.root.config(bg="#ADD8E6")
        self.root.geometry("1100x650")
        
        # Initialize the widgets
        self.init_meas_widgets()
        self.init_graph_widgets()
        
    def init_meas_widgets(self):
        # current
        self.frame1 = LabelFrame(self.root, text="Current (nm)", padx=10, pady=2, bg="gray")
        self.label1 = Entry(self.frame1, bg="white", width=25)
        
        # critical current
        self.frame2 = LabelFrame(self.root, text="Critical Current (nA)", padx=10, pady=2, bg="gray")
        self.label2 = Entry(self.frame2, bg="white", width=25)

        # sample bias voltage
        self.frame3 = LabelFrame(self.root, text="Sample Bias Voltage (V)", padx=10, pady=2, bg="gray")
        self.label3 = Entry(self.frame3, bg="white", width=25)
        
        # critical bias voltage
        self.frame4 = LabelFrame(self.root, text="Critical Bias Voltage (V)", padx=10, pady=2, bg="gray")
        self.label4 = Entry(self.frame4, bg="white", width=25)
        
        # sample rate
        self.frame5 = LabelFrame(self.root, text="Sample Rate", padx=10, pady=2, bg="#7393B3")
        self.label5 = Entry(self.frame5, bg="white", width=25)
        
        # user notes text box
        self.frame7 = LabelFrame(self.root, text="NOTES", padx=10, pady=5, bg="gray")
        self.label7 = Text(self.frame7, height=5, width=30)
        self.label8 = Text(self.frame7, height=1, width=5)
        self.label9 = Label(self.frame7, text="Date:", height=1, width=5)
        
        # setup the drop option menu
        self.DropDownMenu()
        
        # optional graphic parameters
        self.padx = 20
        self.pady = 10
        
        # put on the grid all the elements
        self.publish_meas_widgets()
    
    def publish_meas_widgets(self):
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
    
    def init_graph_widgets(self):
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Tunneling Current (nA)')
        self.fig.set_figwidth(8)
        self.fig.set_figheight(5.5)
        
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
            
            self.ax.set_title('Sample Data Live Graph')
            self.ax.set_xlabel('X Sample Label')
            self.ax.set_ylabel('Y Sample Label')
        except FileNotFoundError:
            pass
