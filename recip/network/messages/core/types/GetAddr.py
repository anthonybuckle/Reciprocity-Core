from recip.network.messages.core.Message import Message
from recip.network.messages.core import MessageType, MessageFactory
from recip.util import Network
from recip.core.Peer import Peer
from recip.storage import Peers
from recip.util import DataType
from recip.util import RLP

class GetAddr(Message):
    def __init__(self):
        super().__init__()
        self.type = MessageType.GETADDR
            
    def send(self):
        payload = Network.sendData(self.addrRecv, self.serialize())
        message = MessageFactory.getInstance(MessageType.ADDR)
        if message.deserialize(payload):
            message.onSuccess()
        else:
            peer = Peer()
            peer.host = self.addrRecv
            Peers.removePeer(peer)
            message.onFailure(self.sendFailure)
            
    def sendFailure(self, message):
        Network.sendData(self.addrRecv, message, False)
            
    def validate(self):
        if self.type != MessageType.GETADDR:
            return False
        return True
            
    def onSuccess(self, callback = None):
        message = MessageFactory.getInstance(MessageType.ADDR)
        peers = Peers.getPeers()
        message.count = len(peers)
        for peer in peers.copy():
            message.addrList.append(peer.host)
        callback(message.serialize())    
    
    def onFailure(self, callback = None):
        peer = Peer()
        peer.host = self.addrFrom
        Peers.removePeer(peer)
        callback(
            'error: Invalid getaddr message'
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