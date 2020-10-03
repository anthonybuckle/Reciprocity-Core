from recip.util.Serializable import Serializable
from recip.util import DataType
from recip.util import RLP

class IndexBlock(Serializable):
    def __init__(self):
        self.chainWork = None
        self.previousHash = None
        self.gasLimit = None
        self.height = None
    
    def serialize(self):
        item = [
            self.chainWork,
            self.previousHash,
            self.gasLimit,
            self.height
        ]
        return RLP.encode(item)
    
    def deserialize(self, buffer):
        decodedBuffer = RLP.decode(buffer)
        self.chainWork = DataType.deserialize(decodedBuffer[0], DataType.INT, 0)
        self.previousHash = decodedBuffer[1]
        self.gasLimit = DataType.deserialize(decodedBuffer[2], DataType.INT, 0)
        self.height = DataType.deserialize(decodedBuffer[3], DataType.INT, 0)