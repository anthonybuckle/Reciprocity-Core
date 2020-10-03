from recip.network.messages.core.Message import Message
from recip.network.messages.core import MessageType
from recip.storage import Peers
from recip.util import DataType
from recip.util import RLP

class VerAck(Message):
    def __init__(self):
        super().__init__()
        self.type = MessageType.VERACK
            
    def send(self):
        pass
            
    def sendFailure(self, message):
        pass
            
    def validate(self):
        if self.type != MessageType.VERACK:
            return False
        return True
            
    def onSuccess(self, callback = None):
        peer = Peers.getPeerByHost(self.addrFrom)
        peer.lastVersionNonce = None
        Peers.addPeer(peer)
    
    def onFailure(self, callback = None):
        callback(
            'error: Invalid verack message'
        )
        
    def serialize(self):
        item = [
            self.type
        ]
        return RLP.encode(item)
    
    def deserialize(self, payload):
        if self.validatePayload(payload, 1):
            self.type = DataType.deserialize(payload[0])
            if self.validate():
                return True
        return False