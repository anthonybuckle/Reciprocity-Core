from recip.network.messages.core.Message import Message
from recip.network.messages.core import MessageType, MessageFactory
from recip.network.messages.core.types.Inv import Inventory, InventoryType
from recip.storage import MemoryPool
from recip.util import Network
from recip.util import DataType
from recip.util import RLP

class MemPool(Message):
    def __init__(self):
        super().__init__()
        self.type = MessageType.MEMPOOL
        
        self.memoryPool = MemoryPool.getMemoryPool()
        
    def send(self):
        payload = Network.sendData(self.addrRecv, self.serialize())
        message = MessageFactory.getInstance(MessageType.INV)
        message.addrRecv = self.addrRecv
        if message.deserialize(payload):
            message.onSuccess()
        else:
            message.onFailure(self.sendFailure)
        
    def sendFailure(self, message):
        pass
        
    def validate(self):
        if self.type != MessageType.MEMPOOL:
            return False
        return True
        
    def onSuccess(self, callback = None):
        message = MessageFactory.getInstance(MessageType.INV)
        inventory = []
        for txId in self.memoryPool:
            unconfirmedTransaction = self.memoryPool[txId]
            inventory.append(Inventory(InventoryType.TRANSACTION, unconfirmedTransaction.hash()))
        message.inventory.extend(inventory)
        callback(message.serialize())
    
    def onFailure(self, callback = None):
        callback(
            'error: Invalid mempool message'
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