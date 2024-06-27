class DataMaster():
    def __init__(self):
        self.ack = "#STATUS_ACK#\n"
        self.nack = "#STATUS_NACK#\n"
        self.succ = "#STATUS_DONE#\n"
        self.fail = "#STATUS_FAIL#\n" 
    
    def DecodeMsg(self):
        temp = self.RowMsg.decode('utf8')
        