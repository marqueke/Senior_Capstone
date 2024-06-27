from GUI_Master_Demo import RootGUI, MeasGUI, GraphGUI, ButtonGUI, ComGUI
from SPI_Data_Ctrl import SerialCtrl

# Initialize serial communication
MySerial = SerialCtrl()

# Initialize the root GUI
RootMaster = RootGUI()

# Initialize other GUI components
GUIMeas = MeasGUI(RootMaster.root)
GUIGraph = GraphGUI(RootMaster.root)
GUIButton = ButtonGUI(RootMaster.root)
ComMaster = ComGUI(RootMaster.root, MySerial)

# Start the Tkinter event loop
RootMaster.root.mainloop()

