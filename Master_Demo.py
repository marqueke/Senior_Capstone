from GUI_Master_Demo import RootGUI, MeasGUI, GraphGUI, ButtonGUI

# Initialize the root GUI
RootMaster = RootGUI()

# Initialize other GUI components
GUIMeas = MeasGUI(RootMaster.root)
GUIGraph = GraphGUI(RootMaster.root)
GUIButton = ButtonGUI(RootMaster.root)

# Start the Tkinter event loop
RootMaster.root.mainloop()

