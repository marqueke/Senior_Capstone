from GUI_Master_Demo import RootGUI, MeasGUI, GraphGUI, ButtonGUI, ComGUI
#from Data_Com_Ctrl import SerialController
from SPI_Data_Ctrl import SerialCtrl

# Initialize the serial controller
MySerial = SerialCtrl()

# Initialize the root GUI
RootMaster = RootGUI()

# Initialize other GUI components
GUIMeas = MeasGUI(RootMaster.root)
GUIGraph = GraphGUI(RootMaster.root)
GUIButton = ButtonGUI(RootMaster.root, RootMaster)
GUICom = ComGUI(RootMaster.root, MySerial, RootMaster)


# Start the Tkinter event loop
RootMaster.root.mainloop()
