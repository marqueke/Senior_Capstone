from GUI_Master_Demo import RootGUI, MeasGUI, GraphGUI, ComGUI

# Initialize the root GUI
RootMaster = RootGUI()

# Initialize other GUI components
GUIMeas = MeasGUI(RootMaster.root, RootMaster)
GUIGraph = GraphGUI(RootMaster.root, GUIMeas)
GUICom = ComGUI(RootMaster.root, RootMaster)

# Link the initialized components to RootMaster
RootMaster.meas_gui = GUIMeas
RootMaster.graph_gui = GUIGraph
RootMaster.com_gui = GUICom

# Ensure MeasGUI has a reference to RootMaster's graph_gui
GUIMeas.parent.graph_gui = GUIGraph

# Start the Tkinter event loop
RootMaster.root.mainloop()

