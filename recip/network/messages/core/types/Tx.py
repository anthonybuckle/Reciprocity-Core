from recip.network.messages.core.Message import Message
from recip.network.messages.core import MessageType
from recip.core.Transaction import Transaction
from recip.storage import MemoryPool
from recip.util import Network
from recip.util import DataType
from recip.util import RLP

class Tx(Message):
    def __init__(self):
        super().__init__()
        self.type = MessageType.TX
        self.transaction = None
        
    def send(self):
        Network.sendData(self.addrRecv, self.serialize(), False)
        
    def sendFailure(self, message):
        pass
        
    def validate(self):
        if self.type != MessageType.TX:
            return False
        if self.transaction == None or len(self.transaction) == 0:
            return False
        return True
        
    def onSuccess(self, callback = None):        
        transaction = Transaction()
        transaction.deserialize(self.transaction)
        if not MemoryPool.addSignedTransaction(transaction):
            self.onFailure(callback)
    
    def onFailure(self, callback = None):
        callback(
            'error: Invalid tx message'
        )
        
    def serialize(self):
        item = [
            self.type,
            self.transaction,
        ]
        return RLP.encode(item)
    
    def deserialize(self, payload):
        if self.validatePayload(payload, 2):
            self.type = DataType.deserialize(payload[0])
            self.transaction = payload[1]
            if self.validate():
                return True
        return False