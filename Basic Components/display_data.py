import tkinter as tk

class SimpleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Entry Example")
        self.root.geometry("300x200")

        self.create_widgets()

    def create_widgets(self):
        # Label to show instructions
        self.label = tk.Label(self.root, text="Enter something and press the button:")
        self.label.pack(pady=10)

        # Entry widget
        self.entry = tk.Entry(self.root, width=30)
        self.entry.pack(pady=10)

        # Button to trigger the print action
        self.button = tk.Button(self.root, text="Print Entry Value", command=self.print_entry_value)
        self.button.pack(pady=10)

        # Label to display the retrieved value
        self.display_label = tk.Label(self.root, text="", bg="white", width=40, height=2)
        self.display_label.pack(pady=10)

    def print_entry_value(self):
        # Retrieve the value from the entry widget
        entry_value = float(self.entry.get())
        # Print the value
        print(f"Entry Value: {entry_value}")
        # Update the display label with the retrieved value
        self.display_label.config(text=f"Entry Value: {entry_value}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleGUI(root)
    root.mainloop()
