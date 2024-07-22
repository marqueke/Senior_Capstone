import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# Generate sample data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Create the figure and axis objects
fig, ax = plt.subplots()

# Plot the data
ax.plot(x, y)

# Set the title and labels
ax.set_title("Sine Wave")
ax.set_xlabel("x-axis")
ax.set_ylabel("y-axis")

# Convert the figure to a NumPy array
fig.canvas.draw()
image_array = np.array(fig.canvas.renderer.buffer_rgba())

# Convert the NumPy array to a PIL Image
image = Image.fromarray(image_array)

# Convert the image to RGB mode
image_rgb = image.convert("RGB")

# Save the RGB image as a JPEG image file
image_rgb.save("output/sine_wave_pil.jpg", format='JPEG')