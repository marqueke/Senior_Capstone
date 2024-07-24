import tkinter as tk

class ExampleApp:
    def __init__(self, root):
        self.root = root
        self.entry = tk.Entry(root)
        self.entry.grid(row=0, column=0)
        self.entry.bind("<Return>", self.handle_enter)
        
    def handle_enter(self, event):
        # Remove focus from the entry widget
        self.root.focus()

if __name__ == "__main__":
    root = tk.Tk()
    app = ExampleApp(root)
    root.mainloop()
