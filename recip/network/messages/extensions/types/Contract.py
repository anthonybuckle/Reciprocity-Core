from recip.network.messages.extensions.ExtMessage import ExtMessage
from recip.network.messages.extensions import ExtMessageType
from recip.core.Contract import Contract as CoreContract
from recip.storage import Contracts
from recip.storage import UXTO
from recip.util import Address
from recip.util import DataType
from recip.util import JSONRPC
from recip.util import Validator
from recip.util import Units

class Contract(ExtMessage):
    def __init__(self):
        super().__init__()
        self.contracts = []
    
    def validate(self):
        if self.contracts == None:
            return False
        for contract in self.contracts:
            if not Validator.address(contract):
                return False
        return True
    
    def deserialize(self, payload):
        if self.validatePayload(payload):
            self.deserializePayload(payload)
            if self.validateParameters():
                for contract in self.params:
                    self.contracts.append(Address.toAddressBytes(contract))
                if self.validate():
                    return True
        return False
    
    def onSuccess(self, callback = None):
        if ExtMessageType.GET_CONTRACTS == self.method:
            self.get(callback)
        elif ExtMessageType.WATCH_CONTRACTS == self.method:
            self.add(callback)
        elif ExtMessageType.DELETE_CONTRACTS == self.method:
            self.remove(callback)
        else:
            self.onFailure(callback)
    
    def get(self, callback = None):
        contracts = []
        for contract in Contracts.getContracts():
            confirmedBalance = 0
            unspentTransactionScript = UXTO.getUnspentTransactionScript(contract.address)
            if unspentTransactionScript != None:
                txOut = unspentTransactionScript.output
                confirmedBalance = txOut.value
            confirmedBalance = Units.toValue(confirmedBalance)
            confirmedBalance = DataType.asFloat(confirmedBalance)
            address = Address.to0xAddress(contract.address)
            contracts.append({
                'address': address,
                'balance': confirmedBalance
            })
        callback(
            JSONRPC.createResultObject(contracts, self.id)
        )
        
    def add(self, callback = None):
        added = False
        for address in self.contracts:
            added = Contracts.addContract(CoreContract(address))
            if not added:
                break
        if added:
            callback(
                JSONRPC.createResultObject('contracts added', self.id)
            )
        else:
            callback(
                JSONRPC.createErrorObject(-32003, 'add failed', 'failed to add contracts', self.id)
            )
    
    def remove(self, callback = None):
        removed = False
        for address in self.contracts:
            removed = Contracts.removeContract(address)
            if not removed:
                break
        if removed:
            callback(
                JSONRPC.createResultObject('contracts removed', self.id)
            )
        else:
            callback(
                JSONRPC.createErrorObject(-32003, 'delete failed', 'failed to remove contracts', self.id)
            )
    
    def onFailure(self, callback = None):
        callback(
            JSONRPC.createErrorObject(-32000, 'invalid message', 'invalid contract request', self.id)
        )