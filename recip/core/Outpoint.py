from recip.util.Serializable import Serializable
from recip.util import DataType
from recip.util import RLP

class Outpoint(Serializable):
    def __init__(self, txId = None, outputIndex = None):
        self.txId = txId
        self.outputIndex = outputIndex

        self.removal = False
        
    def __key(self):
        return (self.txId, self.outputIndex)
    
    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if other == None:
            return self.__key() == other
        return self.__key() == other.__key()
    
    def serialize(self):
        item = [
            self.txId,
            self.outputIndex
        ]
        return RLP.encode(item)
    
    def deserialize(self, buffer):
        decodedBuffer = RLP.decode(buffer)
        self.txId = decodedBuffer[0]
        self.outputIndex = DataType.deserialize(decodedBuffer[1], DataType.INT, 0)  