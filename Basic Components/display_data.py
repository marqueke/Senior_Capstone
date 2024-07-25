import tkinter as tk

class ExampleApp:
    def __init__(self, root):
        self.root = root
        self.create_widgets()

    def create_widgets(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        frame = tk.Frame(self.root, bg='gray')
        frame.grid(row=0, column=0, sticky='nsew')

        for i in range(3):
            self.root.grid_rowconfigure(i, weight=1)
            self.root.grid_columnconfigure(i, weight=1)
            for j in range(3):
                btn = tk.Button(frame, text=f"Button {i},{j}")
                btn.grid(row=i, column=j, sticky='nsew')

        for i in range(3):
            frame.grid_rowconfigure(i, weight=1)
            frame.grid_columnconfigure(i, weight=1)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExampleApp(root)
    root.mainloop()
