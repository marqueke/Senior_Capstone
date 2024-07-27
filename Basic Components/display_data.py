import customtkinter as ctk
from PIL import Image

class ImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hide and Show Image")
        self.root.geometry("300x300")

        # Load the image
        self.image_path = "Images/Start_Btn.png"
        self.image = ctk.CTkImage(Image.open(self.image_path), size=(90, 35))

        # Create a label to display the image
        self.image_label = ctk.CTkLabel(self.root, image=self.image, text='')
        self.image_label.grid(row=0, column=0, padx=10, pady=10)

        # Create buttons to hide and show the image
        self.hide_button = ctk.CTkButton(self.root, text="Hide Image", command=self.hide_image)
        self.hide_button.grid(row=1, column=0, padx=10, pady=10)

        self.show_button = ctk.CTkButton(self.root, text="Show Image", command=self.show_image)
        self.show_button.grid(row=2, column=0, padx=10, pady=10)

    def hide_image(self):
        self.image_label.grid_remove()

    def show_image(self):
        self.image_label.grid()

if __name__ == "__main__":
    root = ctk.CTk()
    app = ImageApp(root)
    root.mainloop()
