from GUI_Master_Demo import RootGUI, MeasGUI, GraphGUI, ComGUI
from Data_Com_Ctrl import DataCtrl
from SPI_Data_Ctrl import SerialCtrl
from SPI_Comm import SerialCtrl, usbMsgFunctions

# Initialize the root GUI
RootMaster = RootGUI()

# Initialize other GUI components
GUIMeas = MeasGUI(RootMaster.root, RootMaster)
GUIGraph = GraphGUI(RootMaster.root)
GUICom = ComGUI(RootMaster.root, RootMaster)


# Start the Tkinter event loop
RootMaster.root.mainloop()