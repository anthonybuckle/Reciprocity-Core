from recip.network.messages.extensions.ExtMessage import ExtMessage
from recip.network.messages.extensions import ExtMessageType
from recip.core.Sidechain import Sidechain as CoreSidechain
from recip.storage import Accounts
from recip.storage import Sidechains
from recip.util import Address
from recip.util import DataType
from recip.util import JSONRPC
from recip.util import Validator
from recip.util import Units

class Sidechain(ExtMessage):
    def __init__(self):
        super().__init__()
        self.sidechains = []
    
    def validate(self):
        if self.sidechains == None:
            return False
        for sidechain in self.sidechains:
            if not Validator.address(sidechain):
                return False
        return True
    
    def deserialize(self, payload):
        if self.validatePayload(payload):
            self.deserializePayload(payload)
            if self.validateParameters():
                for sidechain in self.params:
                    self.sidechains.append(Address.toAddressBytes(sidechain))
                if self.validate():
                    return True
        return False
    
    def onSuccess(self, callback = None):
        if ExtMessageType.GET_SIDECHAINS == self.method:
            self.get(callback)
        elif ExtMessageType.WATCH_SIDECHAIN == self.method:
            self.add(callback)
        elif ExtMessageType.DELETE_SIDECHAINS == self.method:
            self.remove(callback)
        else:
            self.onFailure(callback)
    
    def get(self, callback = None):
        sidechains = []
        for sidechain in Sidechains.getSidechains():
            address = Address.to0xAddress(sidechain.address)
            sidechains.append({
                'address': address
            })
        callback(
            JSONRPC.createResultObject(sidechains, self.id)
        )
        
    def add(self, callback = None):
        added = False
        for address in self.sidechains:
            added = Sidechains.addSidechain(CoreSidechain(address))
            if not added:
                break
        if added:
            callback(
                JSONRPC.createResultObject('sidechains added', self.id)
            )
        else:
            callback(
                JSONRPC.createErrorObject(-32003, 'add failed', 'failed to add sidechains', self.id)
            )
    
    def remove(self, callback = None):
        removed = False
        for address in self.sidechains:
            removed = Sidechains.removeSidechain(address)
            if not removed:
                break
        if removed:
            callback(
                JSONRPC.createResultObject('sidechains removed', self.id)
            )
        else:
            callback(
                JSONRPC.createErrorObject(-32003, 'delete failed', 'failed to remove sidechains', self.id)
            )
    
    def onFailure(self, callback = None):
        callback(
            JSONRPC.createErrorObject(-32000, 'invalid message', 'invalid sidechain request', self.id)
        )