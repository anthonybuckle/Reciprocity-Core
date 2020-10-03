from recip.network.messages.core.Message import Message
from recip.network.messages.core import MessageType, MessageFactory
from recip.network.messages.core.types.Inv import Inventory, InventoryType
from recip.storage import Peers
from recip.util import Chain
from recip.util import Config
from recip.util import Network
from recip.util import DataType
from recip.util import RLP
from recip.util import Validator

class GetBlocks(Message):
    def __init__(self):
        super().__init__()
        self.type = MessageType.GETBLOCKS
        self.version = Config.getIntValue("BLOCK_VERSION")
        self.blockHashes = []
        
        self.chain = Chain.getChain()
        
    def send(self):
        peer = Peers.getPeerByHost(self.addrRecv)
        self.blockHashes.append(peer.chainHeadBlockHash)
        
        payload = Network.sendData(self.addrRecv, self.serialize())
        message = MessageFactory.getInstance(MessageType.INV)
        message.addrFrom = self.addrRecv
        if message.deserialize(payload):
            message.onSuccess()
        else:
            message.onFailure(self.sendFailure)
    
    def sendFailure(self, message):
        pass
        
    def validate(self):
        if self.type != MessageType.GETBLOCKS:
            return False
        if self.version != Config.getIntValue("BLOCK_VERSION"):
            return False
        if self.blockHashes == None or len(self.blockHashes) == 0:
            return False
        for blockHash in self.blockHashes:
            if not Validator.hash(blockHash):
                return False
        return True
        
    def onSuccess(self, callback = None):
        message = MessageFactory.getInstance(MessageType.INV)
        inventory = []
        for blockHash in self.blockHashes:
            previousHash = blockHash
            while previousHash != None:
                block = self.chain.getBlockByHash(previousHash)
                if block != None:
                    inventory.append(Inventory(InventoryType.BLOCK, block.hash()))
                    previousHash = block.previousHash
                else:
                    previousHash = None
        message.inventory.extend(inventory)
        callback(message.serialize())
    
    def onFailure(self, callback = None):
        callback(
            'error: Invalid getblocks message'
        )
        
    def serialize(self):
        item = [
            self.type,
            self.version,
            self.blockHashes
        ]
        return RLP.encode(item)
    
    def deserialize(self, payload):
        if self.validatePayload(payload, 3):
            self.type = DataType.deserialize(payload[0])
            self.version = DataType.deserialize(payload[1], DataType.INT, 0)
            self.blockHashes = payload[2]
            if self.validate():
                return True
        return False