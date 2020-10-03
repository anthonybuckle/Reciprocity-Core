from recip.util.Serializable import Serializable
from recip.core.Output import Output
from recip.util import DataType
from recip.util import RLP

class Coin(Serializable):
    def __init__(self):
        self.output = None
        self.txOutputSize = None
        self.height = None
        self.coinbase = False
    
    def isCoinbase(self):
        return self.coinbase
    
    def serialize(self):
        item = [
            self.output,
            self.txOutputSize,
            self.height,
            self.coinbase
        ]
        return RLP.encode(item)
    
    def deserialize(self, buffer):
        decodedBuffer = RLP.decode(buffer)
        self.output = Output()
        self.output.deserialize(decodedBuffer[0])
        self.txOutputSize = DataType.deserialize(decodedBuffer[1], DataType.INT, 0)
        self.height = DataType.deserialize(decodedBuffer[2], DataType.INT, 0)
        self.coinbase = DataType.deserialize(decodedBuffer[3], DataType.BOOL, False)