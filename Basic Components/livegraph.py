import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import time

# path to fake data
DATA_FILE_PATH = 'fakedata.txt'

style.use('ggplot')

fig = plt.figure()
ax = fig.add_subplot(1,1,1)

def animate(i):
    graph_data = open(DATA_FILE_PATH, 'r').read()
    lines = graph_data.split('\n')
    xdata = []
    ydata = []
    for line in lines:
        if len(line) > 1:
            x, y = line.split(',')
            xdata.append(float(x))
            ydata.append(float(y))
    ax.clear()
    ax.plot(xdata,ydata, c='#64B9FF')
    
    plt.title('Sample Data Live Graph')
    plt.xlabel('X Sample Label')
    plt.ylabel('Y Sample Label')


ani = animation.FuncAnimation(fig, animate, interval=1000, cache_frame_data=False)
plt.show()