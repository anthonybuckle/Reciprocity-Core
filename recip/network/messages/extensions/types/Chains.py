from recip.network.messages.extensions.ExtMessage import ExtMessage
from recip.storage import Accounts
from recip.storage import MemoryPool
from recip.util import Address
from recip.util import JSONRPC
from recip.validate import Validator

class Chains(ExtMessage):
    def __init__(self):
        super().__init__()
        self.fromAddress = None
        self.parameters = None
        self.value = None
        self.gasLimit = None
        self.gasPrice = None
    
    def validate(self):
        if not Validator.address(self.fromAddress):
            return False
        if self.parameters == None or len(self.parameters) == 0:
            return False
        if not Validator.value(self.value):
            return False
        if not Validator.gasLimit(self.gasLimit):
            return False
        if not Validator.gasPrice(self.gasPrice):
            return False
        return True
    
    def deserialize(self, payload):
        if self.validatePayload(payload):
            self.deserializePayload(payload)
            keys = ['fromAddress', 'parameters', 'value', 'gasLimit', 'gasPrice']
            if self.validateParameters(keys):
                self.fromAddress = Address.toAddressBytes(self.params['fromAddress'])
                self.parameters = self.params['parameters']
                self.value = Units.toUnits(self.params['value'])
                self.gasLimit = self.params['gasLimit']
                self.gasPrice = Units.toUnits(self.params['gasPrice'])
                if self.validate():
                    return True
        return False
    
    def onSuccess(self, callback = None):
        fromAccount = Accounts.getAccountByAddress(self.fromAddress)
        txId = None
        if fromAccount != None:
            txId = MemoryPool.addUnconfirmedTransaction(fromAccount, self.toAddress, self.value, self.gasLimit, self.gasPrice)                
        if txId != None:
            callback(
                JSONRPC.createResultObject(DataType.toHex(txId), self.id)
            )
        else:
            self.onFailure(callback)
    
    def onFailure(self, callback = None):
        callback(
            JSONRPC.createErrorObject(-32011, 'invalid message', 'rejected chains', self.id)
        )