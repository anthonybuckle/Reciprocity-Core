from recip.network.messages.extensions.ExtMessage import ExtMessage
from recip.storage import Accounts
from recip.util import Address
from recip.util import Chain
from recip.util import Config
from recip.util import JSONRPC
from recip.util import Validator

class Mining(ExtMessage):
    def __init__(self):
        super().__init__()
        self.address = None
        self.enabled = None
        
        self.chain = Chain.getChain()
    
    def validate(self):
        if not Validator.address(self.address):
            return False
        if self.enabled == None:
            return False
        if not isinstance(self.enabled, bool):
            return False
        return True
    
    def deserialize(self, payload):
        if self.validatePayload(payload):
            self.deserializePayload(payload)
            keys = ['address', 'enabled']
            if self.validateParameters(keys):
                self.address = Address.toAddressBytes(self.params['address'])
                self.enabled = self.params['enabled']
                if self.validate():
                    return True
        return False
    
    def onSuccess(self, callback = None):
        isMiningSupported = Config.getBoolValue("MINING_SUPPORTED")
        if isMiningSupported:
            account = Accounts.getAccountByAddress(self.address)
            if account != None:
                if not self.chain.exitsMiningWorker(account):
                    self.chain.addMiningWorker(account, self.enabled)
                    callback(
                        JSONRPC.createResultObject('added mining worker', self.id)
                    )
                else:
                    if self.enabled:
                        callback(
                            JSONRPC.createResultObject('worker is mining', self.id)
                        )
                    else:
                        self.chain.stopMiningWorker(account)
                        callback(
                            JSONRPC.createResultObject('worker is stopped mining', self.id)
                        )
            else:
                callback(
                    JSONRPC.createErrorObject(-32005, 'not found', 'account not found', self.id)
                )
        else:
            callback(
                JSONRPC.createErrorObject(-32006, 'not supported', 'node does not support mining', self.id)
            )
    
    def onFailure(self, callback = None):
        callback(
            JSONRPC.createErrorObject(-32007, 'invalid message', 'invalid mining request', self.id)
        )
