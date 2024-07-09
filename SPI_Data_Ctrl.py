# Copyright 2021 <WeeW Stack >

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files(the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

# For more content visit the WeeW Stack Channel on YouTube

import serial.tools.list_ports  # pip install pyserial
import serial
# Secure the UART serial communication with MCU
# This will be where the serial connection is decoded

class SerialCtrl():
    def __init__(self):
        '''
        Initializing the main varialbles for the serial data
        '''
        self.ser = None

    def getCOMList(self):
        '''
        Method that get the lost of available coms in the system
        '''
        ports = serial.tools.list_ports.comports()
        self.com_list = [com[0] for com in ports]
        self.com_list.insert(0, "-")

    def SerialOpen(self, ComGUI):
        '''
        Method to setup the serial connection and make sure to go for the next only 
        if the connection is done properly
        '''

        try:
            if self.ser is None:
                PORT = ComGUI.clicked_com.get()
                BAUD = 9600
                self.ser = serial.Serial()
                self.ser.baudrate = BAUD
                self.ser.port = PORT
                self.ser.timeout = 0.1

            if self.ser.is_open:
                print("Already Open")
                self.ser.status = True
            else:
                self.ser.open()
                self.ser.status = True
        except Exception as e:
            print(f"Error opening serial port: {e}")
            self.ser.status = False

    def SerialClose(self, ComGUI):
        '''
        Method used to close the UART communication
        '''
        try:
            self.ser.is_open
            self.ser.close()
            self.ser.status = False
        except Exception as e:
            print(f"Error closing serial port: {e}")
            self.ser.status = False