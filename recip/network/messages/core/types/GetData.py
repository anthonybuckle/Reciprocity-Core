from recip.network.messages.core.Message import Message
from recip.network.messages.core import MessageType, MessageFactory
from recip.network.messages.core.types.Inventory import Inventory
from recip.network.messages.core.types import InventoryType
from recip.storage import MemoryPool
from recip.util import Chain
from recip.util import Network
from recip.util import DataType
from recip.util import RLP

class GetData(Message):
    def __init__(self):
        super().__init__()
        self.type = MessageType.GETDATA
        self.inventory = []
  
        self.chain = Chain.getChain()
        self.memoryPool = MemoryPool.getMemoryPool()
        
    def send(self):
        Network.sendData(self.addrRecv, self.serialize(), False)
        
    def sendFailure(self, message):
        pass
        
    def validate(self):
        if self.type != MessageType.GETDATA:
            return False
        if self.inventory == None or len(self.inventory) == 0:
            return False
        for inv in self.inventory:
            if not inv.validate():
                return False
        return True
        
    def onSuccess(self, callback = None):
        for inventory in self.inventory:
            if inventory.invType == InventoryType.BLOCK:
                message = MessageFactory.getInstance(MessageType.BLOCK)
                block = self.chain.getBlockByHash(inventory.getInvHash())
                message.addrRecv = self.addrFrom
                message.block = block.serialize()
                message.send()
            elif inventory.invType == InventoryType.TRANSACTION:
                message = MessageFactory.getInstance(MessageType.TX)
                txHash = inventory.getInvHash()
                transaction = self.memoryPool[txHash]
                message.addrRecv = self.addrFrom
                message.transaction = transaction.serialize()
                message.send()
    
    def onFailure(self, callback = None):
        callback(
            'error: Invalid getdata message'
        )
        
    def serialize(self):
        inventory = []
        for inv in self.inventory:
            inventory.append(inv.serialize())
        item = [
            self.type,
            inventory
        ]
        return RLP.encode(item)
    
    def deserialize(self, payload):
        if self.validatePayload(payload, 2):
            self.type = DataType.deserialize(payload[0])
            inventoryBytes = payload[1]
            for invBytes in inventoryBytes:
                inventory = Inventory()
                invBytes = RLP.decode(invBytes)
                inventory.deserialize(invBytes)
                self.inventory.append(inventory)
            if self.validate():
                return True
        return False