import serial
import serial.tools.list_ports
import time

ztmComms = serial.Serial(port = "COM8", baudrate=115200,
                         bytesize=8, timeout=3, stopbits=serial.STOPBITS_ONE, write_timeout = 1, parity = serial.PARITY_NONE, xonxoff = 1)
if ztmComms.isOpen():
    ztmComms.close()
ztmComms.open()
ztmComms.isOpen()


time.sleep(1)


def startCalMode():
    MsgId = [0xf]
    padByte = [0x0]
    ztmComms.write(serial.to_bytes(MsgId))#ztmComms.write(MsgId.encode())
    time.sleep(0.05)
    for i in range(0, 9):
        ztmComms.write(serial.to_bytes(padByte))#ztmComms.write(emptyByte.encode())
        time.sleep(0.05)

startCalMode()


msgRcv = ztmComms.read(10)

print(msgRcv)
# THIS WORKED BUT ONLY SENDS ONE BYTE EACH
#ztmUsbTx = [0x07, 0x04, 0x05]
#ztmComms.write(serial.to_bytes(ztmUsbTx))
#
#time.sleep(0.05)
#ztmUsbRx = [0x0e, 0x04, 0x05]
#ztmComms.write(serial.to_bytes(ztmUsbRx))


#for i in ztmUsbTx:
#    txByte=i
#    print(txByte)
#    #ztmComms.write(txByte)
#    #time.sleep(0.05)

ztmComms.close()