from recip.network.messages.core.Message import Message
from recip.network.messages.core import MessageType, MessageFactory
from recip.core.Peer import Peer
from recip.storage import Peers
from recip.util import Chain
from recip.util import Config
from recip.util import Network
from random import randint
from recip.util import DataType
from recip.util import Sync
from recip.util import RLP
from recip.util import Validator
import sys

class Version(Message):
    def __init__(self):
        super().__init__()
        self.type = MessageType.VERSION
        self.version = Config.getValue("NODE_VERSION")
        self.timestamp = DataType.asTime()
        self.nonce = randint(0, sys.maxsize)
        self.chainHeadBlockHash = None
    
    def send(self):
        peer = Peers.getPeerByHost(self.addrRecv)
        if peer.lastVersionNonce == None:
            peer.lastVersionNonce = self.nonce
            Peers.addPeer(peer)
        else:
            self.nonce = peer.lastVersionNonce 
        
        chainHeadBlock = Chain.getChain().getChainHeadBlock()
        self.chainHeadBlockHash = chainHeadBlock.hash()
        
        payload = Network.sendData(self.addrRecv, self.serialize())
        message = MessageFactory.getInstance(MessageType.VERACK)
        message.addrFrom = self.addrRecv
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
        if self.type != MessageType.VERSION:
            return False
        if self.version != Config.getValue("NODE_VERSION"):
            return False
        if self.timestamp == None or self.timestamp < 0:
            return False
        if self.nonce == None or self.nonce < 0:
            return False
        if not Validator.hash(self.chainHeadBlockHash):
            return False
        return True
    
    def onSuccess(self, callback = None):
        peer = Peers.getPeerByHost(self.addrFrom)
        syncVersion = False
        if peer == None:
            peer = Peer()
        else:
            syncVersion = peer.lastVersionNonce == None
        if peer.lastVersionNonce == None or peer.lastVersionNonce == self.nonce:
            peer.host = self.addrFrom
            peer.version = self.version
            peer.lastVersionNonce = self.nonce
            peer.chainHeadBlockHash = self.chainHeadBlockHash
            Peers.addPeer(peer)
            if syncVersion:
                Sync.synchronizeMessage(MessageType.VERSION, peer.host)
        message = MessageFactory.getInstance(MessageType.VERACK)
        callback(message.serialize())        
    
    def onFailure(self, callback = None):
        peer = Peer()
        peer.host = self.addrFrom
        Peers.removePeer(peer)
        callback(
            'error: Invalid version message'
        )
        
    def serialize(self):
        item = [
            self.type,
            self.version,
            self.timestamp,
            self.nonce,
            self.chainHeadBlockHash
        ]
        return RLP.encode(item)
    
    def deserialize(self, payload):
        if self.validatePayload(payload, 5):
            self.type = DataType.deserialize(payload[0])
            self.version = DataType.deserialize(payload[1])
            self.timestamp = DataType.deserialize(payload[2], DataType.INT, 0)
            self.nonce = DataType.deserialize(payload[3], DataType.INT, 0)
            self.chainHeadBlockHash = payload[4]
            if self.validate():
                return True
        return False