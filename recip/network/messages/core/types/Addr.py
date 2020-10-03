from recip.network.messages.core.Message import Message
from recip.network.messages.core import MessageType
from recip.storage import Peers
from recip.core.Peer import Peer
from recip.util import Network
from recip.util import DataType
from recip.util import RLP
from recip.util import Validator

class Addr(Message):
    def __init__(self):
        super().__init__()
        self.type = MessageType.ADDR
        self.addrList = []
        
    def send(self):
        self.addrList.append(self.addrFrom)
        Network.sendData(self.addrRecv, self.serialize(), False)
    
    def sendFailure(self, message):
        pass
        
    def validate(self):
        if self.type != MessageType.ADDR:
            return False
        if self.addrList == None or len(self.addrList) == 0:
            return False
        for addr in self.addrList:
            if not Validator.host(addr):
                return False
        return True
        
    def onSuccess(self, callback = None):
        if len(self.addrList) > 0:
            peers = []
            for addr in self.addrList:
                peer = Peer()
                peer.host = addr
                peers.append(peer)
            Peers.addPeers(peers)
            
    def onFailure(self, callback = None):
        callback(
            'error: Invalid addr message'
        )
        
    def serialize(self):
        item = [
            self.type,
            self.addrList
        ]
        return RLP.encode(item)
    
    def deserialize(self, payload):
        if self.validatePayload(payload, 2):
            self.type = DataType.deserialize(payload[0])
            self.addrList = DataType.deserialize(payload[1], DataType.LIST, [])
            if self.validate():
                return True
        return False