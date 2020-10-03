from recip.network.messages.core.Message import Message
from recip.network.messages.core import MessageType
from recip.util import DataType
from recip.util import RLP

class Pong(Message):
    def __init__(self):
        super().__init__()
        self.type = MessageType.PONG
        self.nonce = None
        
    def send(self):
        pass
        
    def sendFailure(self, message):
        pass
        
    def validate(self):
        if self.type != MessageType.PONG:
            return False
        if self.nonce == None or self.nonce < 0:
            return False
        return True
        
    def onSuccess(self, callback = None):
        pass
    
    def onFailure(self, callback = None):
        callback(
            'error: Invalid pong message'
        )
        
    def serialize(self):
        item = [
            self.type,
            self.nonce
        ]
        return RLP.encode(item)
    
    def deserialize(self, payload):
        if self.validatePayload(payload, 2):
            self.type = DataType.deserialize(payload[0])
            self.nonce = DataType.deserialize(payload[1], DataType.INT, 0)
            if self.validate():
                return True
        return False