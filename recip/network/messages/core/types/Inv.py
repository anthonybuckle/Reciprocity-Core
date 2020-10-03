from recip.network.messages.core.Message import Message
from recip.network.messages.core import MessageType, MessageFactory
from recip.network.messages.core.types.Inventory import Inventory
from recip.network.messages.core.types import InventoryType
from recip.storage import MemoryPool
from recip.util import Chain
from recip.util import Network
from recip.util import DataType
from recip.util import RLP

class Inv(Message):
    def __init__(self):
        super().__init__()
        self.type = MessageType.INV
        self.inventory = []
        
        self.chain = Chain.getChain()

    def send(self):
        Network.sendData(self.addrRecv, self.serialize(), False)

    def sendFailure(self, message):
        pass

    def validate(self):
        if self.type != MessageType.INV:
            return False
        if self.inventory == None or len(self.inventory) == 0:
            return False
        for inv in self.inventory:
            if not inv.validate():
                return False
        return True

    def onSuccess(self, callback = None):
        message = MessageFactory.getInstance(MessageType.GETDATA)
        message.addrRecv = self.addrFrom
        for inventory in self.inventory:
            if inventory.invType == InventoryType.BLOCK:
                if self.chain.getBlockByHash(inventory.getInvHash()) == None:
                    message.inventory.append(inventory)
            elif inventory.invType == InventoryType.TRANSACTION:
                if MemoryPool.getTransactionById(inventory.getInvHash()) == None:
                    message.inventory.append(inventory)
        if len(message.inventory) > 0:
            message.send()
    
    def onFailure(self, callback = None):
        callback(
            'error: Invalid inv message'
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