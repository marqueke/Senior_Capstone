from tkinter import *

class RootGUI:
    def __init__(self):
        self.root = Tk()
        self.root.title("Homepage")
        self.root.config(bg="skyblue")
        self.root.geometry("1000x650")

# widget for measurements in homepage
class MeasGUI():
    def __init__(self,root):
        self.root = root
        
        # current measurement
        self.frame1 = LabelFrame(root, text = "Current Measurement (nA)", 
                                padx=10, pady=1, bg="gray")
        self.label1 = Entry(self.frame1, bg="white", width=25)
        
        # critical current
        self.frame2 = LabelFrame(root, text = "Critical Measurement (nA)", 
                                padx=10, pady=1, bg="gray")
        self.label2 = Entry(self.frame2, bg="white", width=25)
        
        # current distance
        self.frame3 = LabelFrame(root, text="Current Distance (nm)", 
                                 padx=10, pady=1, bg="gray")
        self.label3 = Entry(self.frame3, bg="white", width=25)
        
        # critical distance
        self.frame4 = LabelFrame(root, text="Critical Distance (nm)", 
                                 padx=10, pady=1, bg="gray")
        self.label4 = Entry(self.frame4, bg="white", width=25)
        
        # current setpoint
        self.frame5 = LabelFrame(root, text="Current Setpoint (nA)", 
                                 padx=10, pady=1, bg="gray")
        self.label5 = Entry(self.frame5, bg="white", width=25)
        
        # current offset
        self.frame6 = LabelFrame(root, text="Current Offset (nA)", 
                                 padx=10, pady=1, bg="gray")
        self.label6 = Entry(self.frame6, bg="white", width=25)
        
        # setup the drop option menu
        self.DropDownMenu()
        
        # optional graphic parameters
        self.padx=20
        self.pady=5
        
        # put on the grid all the elements
        self.publish()
    
    def publish(self):
        self.frame1.grid(row=10, column=2, padx=5, pady=5, sticky=S)
        self.label1.grid(row=2, column=1)
        
        self.frame2.grid(row=11, column=2, padx=5, pady=5)
        self.label2.grid(row=2, column=1)   
        
        self.frame3.grid(row=10, column=3, padx=5, pady=5)
        self.label3.grid(row=2, column=1) 
        
        self.frame4.grid(row=11, column=3, padx=5, pady=5)
        self.label4.grid(row=2, column=1) 
        
        self.frame5.grid(row=10, column=4, padx=5, pady=5)
        self.label5.grid(row=2, column=1) 
        
        self.frame6.grid(row=11, column=4,padx=5, pady=5)
        self.label6.grid(row=2, column=1) 
        
        # file drop-down menu
        self.drop_menu.grid(row=0,column=0, padx=self.padx, pady=self.pady)
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
 
         
if __name__ == "__main__":
    root_gui = RootGUI()
    MeasGUI(root_gui)
