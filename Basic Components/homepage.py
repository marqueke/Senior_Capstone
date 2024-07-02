# import modules
from tkinter import *

# create homepage window
root = Tk()
root.title("Homepage")
root.config(bg="skyblue")

#set geometry
root.geometry("1000x650")

# label for graph
graph_name = Label(root, text = "Live Graph", bg = "skyblue").place(x=250, y=5)

# create frame widget
home_frame = Frame(root, width = 500, height = 300).place(x = 50, y = 25)
#home_frame.pack(pady = 25)

# create graph frame within left_frame
graph_frame = Frame(home_frame, width = 490, height = 290, bg="gray").place(x = 55, y = 30)
#graph_frame.pack(padx = 5, pady = 5)

# create label above home frame
# Label(root, text="Graphs").grid(row=1, column=0, padx=5, pady=5)

root.mainloop()