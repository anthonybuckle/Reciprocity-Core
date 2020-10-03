from recip.util.Serializable import Serializable

class Opcode(Serializable):
    def __init__(self):
        self.name = None
        self.code = None
        self.method = None
        self.index = None
        self.gas = None
        
    def serialize(self):
        return [
            self.name,
            self.code,
            self.method,
            self.index,
            self.gas
        ]
    
    def deserialize(self, buffer):
        self.name = buffer[0]
        self.code = buffer[1]
        self.method = buffer[2]
        self.index = buffer[3]
        self.gas = buffer[4]