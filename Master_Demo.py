from GUI_Master_Demo import RootGUI, MeasGUI, GraphGUI, ButtonGUI

RootMaster = RootGUI()
GUIMeas = MeasGUI(RootMaster.root)
GUIGraph = GraphGUI(RootMaster.root)
GUIButton = ButtonGUI(RootMaster.root)

RootMaster.root.mainloop()