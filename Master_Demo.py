from GUI_Master_Demo import RootGUI, MeasGUI, GraphGUI, ButtonGUI, ComGUI
from Data_Com_Ctrl import SerialController
from SPI_Data_Ctrl import SerialCtrl

MySerial = SerialCtrl()

# Initialize the root GUI
RootMaster = RootGUI()

# Initialize other GUI components
GUIMeas = MeasGUI(RootMaster.root)
GUIGraph = GraphGUI(RootMaster.root)
GUIButton = ButtonGUI(RootMaster.root)
GUICom = ComGUI(RootMaster.root, MySerial)

'''
# Initialize serial communication and start reading
MySerial = SerialController(
    port='COM7',         # Update with your COM port
    baudrate=9600,
    callback=GUIMeas.update_distance
)
MySerial.start(RootMaster.root)

# Initialize ComGUI with the serial controller
ComMaster = ComGUI(RootMaster.root, MySerial)

# Ensure the serial communication stops when the application quits
def on_closing():
    MySerial.stop()
    RootMaster.root.quit()

RootMaster.root.protocol("WM_DELETE_WINDOW", on_closing)
'''


# Start the Tkinter event loop
RootMaster.root.mainloop()
