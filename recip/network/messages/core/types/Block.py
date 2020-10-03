from recip.network.messages.core.Message import Message
from recip.network.messages.core import MessageType
from recip.core.Block import Block as CoreBlock
from recip.util import Chain
from recip.util import Network
from recip.util import DataType
from recip.util import RLP

class Block(Message):
    def __init__(self):
        super().__init__()
        self.type = MessageType.BLOCK
        self.block = None
 
    def send(self):
        Network.sendData(self.addrRecv, self.serialize(), False)
 
    def sendFailure(self, message):
        pass
 
    def validate(self):
        if self.type != MessageType.BLOCK:
            return False
        if self.block == None or len(self.block) == 0:
            return False
        return True
 
    def onSuccess(self, callback = None):
        block = CoreBlock()
        block.deserialize(self.block)
        if not Chain.getChain().addBlock(block):
            self.onFailure(callback)
    
    def onFailure(self, callback = None):
        callback(
            'error: Invalid block message'
        )
        
    def serialize(self):
        item = [
            self.type,
            self.block,
        ]
        return RLP.encode(item)
    
    def deserialize(self, payload):
        if self.validatePayload(payload, 2):
            self.type = DataType.deserialize(payload[0])
            self.block = payload[1]
            if self.validate():
                return True
        return False