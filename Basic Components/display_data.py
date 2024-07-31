import time
import random
import tkinter as tk


class TempView(tk.Frame):
    def __init__(self, master):
        super().__init__(master)     # call base class
        self.label1_text = tk.StringVar()
        self.label1_text.set("initial value")
        self.label1=tk.Label(self.master, textvariable=self.label1_text,
                            fg='blue', font=("Arial", 18, "bold"),
                            background='#CDC5D9')
        self.label1.grid(row=0,column=0)
 
        self.master.grid_columnconfigure(1, minsize=100)
 
        tk.Button(self.master, text="Quit", command=self.master.destroy,
                  bg="red").grid(row=1, column=0)
 
        ## update the label in two different ways
        self.getTemp()
    
    def getTemp(self):
        temp = str(random.randint(10, 100))
        self.update(temp)
        self.master.after(2000, self.getTemp) ## sleep for 2 seconds
 
    def update(self, temp):
        self.label1_text.set(temp)
        print(F"The temperature is {temp}")

random.seed()
root = tk.Tk()
app = TempView(master=root)
app.mainloop()