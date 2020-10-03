from recip.util.Serializable import Serializable
from recip.util import Config
from recip.util import DataType
from recip.util import RLP
from recip.util import Validator

class Peer(Serializable):
    def __init__(self):
        self.host = None
        self.version = None
        self.lastVersionNonce = None
        self.chainHeadBlockHash = None
        self.lastUpdate = None
    
    def validate(self):
        if self.host == None or len(self.host) == 0:
            return False
        if self.version != Config.getValue("NODE_VERSION"):
            return False
        if self.lastVersionNonce == None or self.lastVersionNonce < 0:
            return False
        if not Validator.hash(self.chainHeadBlockHash):
            return False
        if self.lastUpdate == None or self.lastUpdate < 0:
            return False
        return True
        
    def __key(self):
        return (self.host)
    
    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if other == None:
            return self.__key() == other
        return self.__key() == other.__key()
    
    def merge(self, peer):
        if peer.host != None:
            self.host = peer.host
        if peer.version != None:
            self.version = peer.version
            
        self.lastVersionNonce = peer.lastVersionNonce
            
        if peer.chainHeadBlockHash != None:
            self.chainHeadBlockHash = peer.chainHeadBlockHash
        if peer.lastUpdate != None:
            self.lastUpdate = peer.lastUpdate
    
    def serialize(self):
        item = [
            self.host,
            self.version,
            self.lastVersionNonce,
            self.chainHeadBlockHash,
            self.lastUpdate
        ]
        return RLP.encode(item)
    
    def deserialize(self, buffer):
        decodedBuffer = RLP.decode(buffer)
        self.host = DataType.deserialize(decodedBuffer[0])
        self.version = DataType.deserialize(decodedBuffer[1])
        self.lastVersionNonce = DataType.deserialize(decodedBuffer[2], DataType.INT, None) 
        self.chainHeadBlockHash = decodedBuffer[3]
        self.lastUpdate = DataType.deserialize(decodedBuffer[4], DataType.INT, 0)