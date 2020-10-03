from recip.network.messages.extensions.ExtMessage import ExtMessage
from recip.network.messages.extensions import ExtMessageType
from recip.core.Peer import Peer as CorePeer
from recip.storage import Peers
from recip.util import Network
from recip.util import JSONRPC
from recip.util import Validator

class Peer(ExtMessage):
    def __init__(self):
        super().__init__()
        self.hosts = []
    
    def validate(self):
        if self.hosts == None:
            return False
        for host in self.hosts:
            if not Validator.host(host):
                return False
        return True
    
    def deserialize(self, payload):
        if self.validatePayload(payload):
            self.deserializePayload(payload)
            if self.validateParameters():
                for host in self.params:
                    self.hosts.append(host)
                if self.validate():
                    return True
        return False
    
    def onSuccess(self, callback = None):
        if ExtMessageType.GET_PEERS == self.method:
            self.get(callback)
        elif ExtMessageType.ADD_PEERS == self.method:
            self.add(callback)
        elif ExtMessageType.DELETE_PEERS == self.method:
            self.remove(callback)
        else:
            self.onFailure(callback)
    
    def get(self, callback = None):         
        peers = []
        for peer in Peers.getPeers():
            peers.append(peer.host)
        callback(
            JSONRPC.createResultObject(peers, self.id)
        )
      
    def add(self, callback = None):      
        peers = []
        for host in self.hosts:
            peer = CorePeer()
            if not ':' in host:
                host += "{0}{1}".format(':', Network.getSocketPort())
            peer.host = host
            peers.append(peer)
        Peers.addPeers(peers)
        callback(
            JSONRPC.createResultObject('added peers', self.id)
        )
        
    def remove(self, callback = None):  
        peers = []
        for host in self.hosts:
            peer = CorePeer()
            peer.host = host
            peers.append(peer)
        Peers.removePeers(peers)
        callback(
            JSONRPC.createResultObject('removed peers', self.id)
        )
            
    def onFailure(self, callback = None):
        callback(
            JSONRPC.createErrorObject(-32009, 'invalid message', 'invalid peer request', self.id)
        )