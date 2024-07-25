# Imports tkinter
from tkinter import *

# toplevel window
root = Tk()

# label widget
label = Label(root, text="LABEL")


# Method to make Label(Widget) invisible
def hide_label():
    # This will remove the widget
    label.pack_forget()


# Method to make Label(widget) visible
def recover_label():
    # This will recover the widget
    label.pack()


# hide_label() function hide the label temporarily
B2 = Button(root, text="Click To Hide label", fg="red", command=hide_label)
B2.pack()

# recover_label() function recover the label
B1 = Button(root, text="Click To Show label",
            fg="green", command=recover_label)
B1.pack()

# pack Label widget
label.pack()

# Start the GUI
root.mainloop()
