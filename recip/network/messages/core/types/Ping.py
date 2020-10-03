from recip.network.messages.core.Message import Message
from recip.network.messages.core import MessageType, MessageFactory
from recip.util import Network
from recip.core.Peer import Peer
from recip.storage import Peers
from random import randint
from recip.util import RLP
from recip.util import DataType
import sys

class Ping(Message):
    def __init__(self):
        super().__init__()
        self.type = MessageType.PING
        self.nonce = randint(0, sys.maxsize)
        
    def send(self):
        payload = Network.sendData(self.addrRecv, self.serialize())
        isValid = True
        message = MessageFactory.getInstance(MessageType.PONG)
        if message.deserialize(payload):
            if message.nonce == self.nonce:
                message.onSuccess()
            else:
                isValid = False 
        else:
            isValid = False 
        if isValid == False:
            peer = Peer()
            peer.host = self.addrRecv
            Peers.removePeer(peer)
            message.onFailure(self.sendFailure)
            
    def sendFailure(self, message):
        Network.sendData(self.addrRecv, message, False)
        
    def validate(self):
        if self.type != MessageType.PING:
            return False
        if self.nonce == None or self.nonce < 0:
            return False
        return True
        
    def onSuccess(self, callback = None):
        message = MessageFactory.getInstance(MessageType.PONG)
        message.nonce = self.nonce
        callback(message.serialize())        
    
    def onFailure(self, callback = None):
        peer = Peer()
        peer.host = self.addrFrom
        Peers.removePeer(peer)
        callback(
            'error: Invalid ping message'
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