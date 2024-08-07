#import serial
#import threading
import queue
import globals
import asyncio
import serial_asyncio

class SerialCtrl:
    def __init__(self, port, baudrate):
        self.port = port
        self.serial_port = None
        self.baudrate = baudrate
        self.send_queue = queue.Queue()  # Queue for data to be sent
        self.receive_queue = asyncio.Queue()  # Async Queue for received data
        self.send_task = None
        self.receive_task = None

    async def start(self):
        try:
            loop = asyncio.get_running_loop()
            self.serial_port, _ = await serial_asyncio.open_serial_connection(
                url=self.port,
                baudrate=self.baudrate,
                loop=loop
            )
            asyncio.create_task(self.receive_serial())  # Start receiving serial data
            asyncio.create_task(self.send_serial())  # Start sending serial data
        
            return True
        except Exception as e:
            print(f"Error opening serial port: {e}")
            self.serial_port = None
            return False


    async def stop(self):
        if self.send_task:
            self.send_task.cancel()
        if self.receive_task:
            self.receive_task.cancel()
        if self.serial_port:
            await self.serial_port.close()
        #print("Serial communication stopped.")
            
    async def receive_serial(self):
        while True:
            try:
                data = await self.serial_port.read(globals.MSG_BYTES)
                if data:
                    await self.receive_queue.put(data)
                    # Process the data as needed
            except Exception as e:
                print(f"Error reading serial port: {e}")
                break

    async def send_serial(self):
        while True:
            data = await self.send_queue.get()  # Async get from queue
            if data:
                try:
                    self.serial_port.write(data)
                except Exception as e:
                    print(f"Error writing to serial port: {e}")
    
    async def ztmGetMsg(self):
        """
        Asynchronously attempts to read a message from the ZTM controller.
        """
        attempts = 0
        #response = b''  # Initialize an empty byte string to store the response
        while attempts < globals.MAX_ATTEMPTS:
            try:
                # Use asyncio's read method
                response = await self.serial_port.read(globals.MSG_BYTES)
                if response and len(response) == globals.MSG_BYTES:
                    return response
            except Exception as e:
                #print(f"Read operation failed: {e}")    
                attempts += 1      
                await asyncio.sleep(0.01)   # Introduce a small delay between attempts
        return None






'''
# OLD METHOD
class SerialCtrl:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.serial_port = None
        self.send_thread = None
        self.receive_thread = None
        self.send_queue = queue.Queue()  # Queue for data to be sent
        self.receive_queue = queue.Queue()  # Queue for received data
        self.send_running = False
        self.receive_running = False

    def ztmGetMsg(self):
        # Attempt to read a message from the ZTM controller
        
        attempts = 0
        #response = b''  # Initialize an empty byte string to store the response
        while(attempts < globals.MAX_ATTEMPTS):
            try:
                response = self.serial_port.read(globals.MSG_BYTES)
                return response
            except serial.SerialException as e:
                #print(f"Read operation failed: {e}")    
                attempts += 1        
        if attempts == globals.MAX_ATTEMPTS:
            #print(f"Failed to receive complete message.\n")   
            return False
        
    def receive_serial(self):
        """
        Continuously reads data from the serial port and processes it.
        """
        while self.receive_running:
            try:
                if self.serial_port.in_waiting > 0:
                    raw_data = self.serial_port.read(self.serial_port.in_waiting)
                    self.receive_queue.put(raw_data)  # Push received data to queue
                    #print(f"Received data: {raw_data.hex()}")
                    return raw_data
            except serial.SerialException as e:
                print(f"Error reading serial port: {e}")
                self.receive_running = False

    def send_serial(self):
        """
        Continuously sends data from the send queue to the serial port.
        """
        while self.send_running:
            try:
                data = self.send_queue.get(timeout=0.01)  # Wait for data with a timeout
                if data:
                    self.serial_port.write(data)
                    #print(f"Sent data: {data.hex()}")
            except queue.Empty:
                continue  # No data to send, loop back
            #except serial.SerialException as e:
                #print(f"Failed to write to serial port: {e}")

    def start(self):
        try:
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.01,  # Set a timeout for read operations
                write_timeout=0.01,  # Set a timeout for write operations
                xonxoff=False,
                rtscts=True,
            )
            # Increase the read and write buffer sizes
            self.serial_port.set_buffer_size(rx_size=65536, tx_size=65536)
            
            self.send_running = True
            self.receive_running = True
            self.send_thread = threading.Thread(target=self.send_serial)
            self.receive_thread = threading.Thread(target=self.receive_serial)
            self.send_thread.start()
            self.receive_thread.start()
            #print("Send and receive threads started.")
            return True
        except serial.SerialException as e:
            #print(f"Error opening serial port: {e}")
            self.serial_port = None
            return False

    def stop(self):
        self.send_running = False
        self.receive_running = False
        if self.serial_port:
            self.send_thread.join()
            self.receive_thread.join()
            self.serial_port.close()
            #print("Serial communication stopped.")

    def queue_data_for_sending(self, data):
        """
        Adds data to the send queue to be sent by the send thread.
        """
        self.send_queue.put(data)

    def get_received_data(self):
        """
        Retrieves the next available data from the receive queue.
        """
        try:
            return self.receive_queue.get_nowait()
        except queue.Empty:
            return None
'''           