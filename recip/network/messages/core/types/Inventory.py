from recip.util.Serializable import Serializable
from recip.util import DataType
from recip.util import RLP
from recip.util import Validator

class Inventory(Serializable):
    def __init__(self, invType = None, invHash = None):
        self.invType = invType
        self.invHash = invHash
        
    def validate(self):
        if self.invType == None or len(self.invType) == 0:
            return False
        if not Validator.hash(self.invHash):
            return False
        return True
    
    def getInvType(self):
        return self.invType
    
    def getInvHash(self):
        return self.invHash
        
    def serialize(self):
        item = [
            self.invType,
            self.invHash
        ]
        return RLP.encode(item)
    
    def deserialize(self, payload):
        if payload != None and len(payload) == 2:
            self.invType = DataType.deserialize(payload[0])
            self.invHash = payload[1]
            if self.validate():
                return True
        return False