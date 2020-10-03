from recip.util.Serializable import Serializable
from recip.core.Transaction import Transaction
from recip.util import Crypto
from recip.util import Config
from recip.util import DataType
from recip.util import RLP

class Block(Serializable):
    def __init__(self):
        self.version = Config.getIntValue("BLOCK_VERSION")
        self.previousHash = None
        self.merkleRoot = None
        self.witnessRoot = None
        self.gasLimit = None
        self.gasUsed = None
        self.nonce = None
        self.bits = None
        self.timestamp = DataType.asTime()
        self.transactions = []
        
    def hash(self):
        return Crypto.proofOfWorkHash(self.serializeHeader())
    
    def getHeader(self):
        item = [
            self.version,
            self.previousHash,
            self.merkleRoot,
            self.witnessRoot,
            self.gasLimit,
            self.gasUsed,
            self.nonce,
            self.bits,
            self.timestamp
        ]
        return item
    
    def getBody(self):
        return self.transactions
    
    def serializeHeader(self):
        header = self.getHeader()
        return RLP.encode(header)
    
    def serialize(self):
        item = self.getHeader()
        item.append(self.getBody())
        return RLP.encode(item)
    
    def deserialize(self, buffer):
        decodedBuffer = RLP.decode(buffer)
        self.version = DataType.deserialize(decodedBuffer[0], DataType.INT, 0)
        self.previousHash = decodedBuffer[1]
        self.merkleRoot = decodedBuffer[2]
        self.witnessRoot = decodedBuffer[3]
        self.gasLimit = DataType.deserialize(decodedBuffer[4], DataType.INT, 0)
        self.gasUsed = DataType.deserialize(decodedBuffer[5], DataType.INT, 0)
        self.nonce = DataType.deserialize(decodedBuffer[6], DataType.INT, 0)
        self.bits = DataType.deserialize(decodedBuffer[7], DataType.INT, 0)
        self.timestamp = DataType.deserialize(decodedBuffer[8], DataType.INT, 0)
        self.transactions = []
        for txBuffer in decodedBuffer[9]:
            transaction = Transaction()
            transaction.deserialize(txBuffer)
            self.transactions.append(transaction)
