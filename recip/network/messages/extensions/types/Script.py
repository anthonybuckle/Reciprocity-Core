from recip.network.messages.extensions.ExtMessage import ExtMessage
from recip.network.messages.extensions import ExtMessageType
from recip.core.Contract import Contract
from recip.core.Input import Input
from recip.core.Output import Output
from recip.core.Transaction import Transaction
from recip.storage import Accounts
from recip.storage import Contracts
from recip.storage import MemoryPool
from recip.storage import PersistentStorage
from recip.storage import UXTO
from recip.util import Address
from recip.util import Config
from recip.util import Crypto
from recip.util import DataType
from recip.util import JSONRPC
from recip.util import Validator
from recip.util import Units
from recip.vm.RVM import RVM

class Script(ExtMessage):
    def __init__(self):
        super().__init__()
        self.fromAddress = None
        self.script = None
        self.parameters = None
        self.value = None
        self.gasLimit = None
        self.gasPrice = None
    
    def validate(self):
        if not Validator.address(self.fromAddress):
            return False
        if self.script == None or len(self.script) == 0:
            return False
        if self.parameters == None:
            return False
        if not Validator.value(self.value, True):
            return False
        if not Validator.gasLimit(self.gasLimit):
            return False
        if not Validator.gasPrice(self.gasPrice):
            return False
        return True
    
    def deserialize(self, payload):
        if self.validatePayload(payload):
            self.deserializePayload(payload)
            keys = ['fromAddress', 'script', 'parameters', 'value', 'gasLimit', 'gasPrice']
            if self.validateParameters(keys):
                self.fromAddress = Address.toAddressBytes(self.params['fromAddress'])
                if self.isDeploy():
                    self.script = DataType.fromHex(self.params['script'])
                else:
                    self.script = Address.toAddressBytes(self.params['script'])
                self.parameters = self.params['parameters']
                self.value = Units.toUnits(self.params['value'])
                self.gasLimit = self.params['gasLimit']
                self.gasPrice = Units.toUnits(self.params['gasPrice'])
                if self.validate():
                    return True
        return False
    
    def onSuccess(self, callback = None):
        if ExtMessageType.DEPLOY_SCRIPT == self.method:
            self.deploy(False, callback)
        elif ExtMessageType.DEPLOY_LOCAL_SCRIPT == self.method:
            self.deploy(True, callback)
        elif ExtMessageType.CALL_TX_SCRIPT == self.method:
            self.call(False, callback)
        elif ExtMessageType.CALL_LOCAL_SCRIPT == self.method:
            self.call(True, callback)
        elif ExtMessageType.GET_SCRIPT_LOGS == self.method:
            self.logs(callback)
        else:
            self.onFailure(callback)
        
    def isDeploy(self):
        if ExtMessageType.DEPLOY_SCRIPT == self.method:
            return True
        elif ExtMessageType.DEPLOY_LOCAL_SCRIPT == self.method:
            return True
        return False

    def deploy(self, isLocal, callback):
        result = None
        fromAccount = Accounts.getAccountByAddress(self.fromAddress)
        if fromAccount != None:
            if isLocal:
                toAddress = Crypto.generateAddress(fromAccount.address)

                _script = bytearray()
                _script.append(Config.getIntValue("EXTENSION_SCRIPT_VERSION"))
                _script.extend(self.script)
                _script = DataType.serialize(_script)

                extraData = None
                if len(self.parameters) > 0:
                    extraData = self.parameters
                    extraData.append(fromAccount.address)

                output = Output(toAddress, _script, self.value, extraData)

                result = self.handleLocalScript(fromAccount, output, True)
                if result != None:
                    Contracts.addContract(Contract(toAddress), False)
            else:
                result = MemoryPool.addUnconfirmedTransaction(fromAccount, None, self.value, self.gasLimit, self.gasPrice, self.script, self.parameters)                
                try:
                    result = DataType.toHex(result)
                except:
                    pass
        if result != None:
            callback(
                JSONRPC.createResultObject(result, self.id)
            )
        else:
            self.onFailure(callback)
            
    def call(self, isLocal, callback):
        result = None
        fromAccount = Accounts.getAccountByAddress(self.fromAddress)
        if fromAccount != None:
            if isLocal:
                _output = PersistentStorage.get(self.script, True)
                if _output == None:
                    unspentTransactionScript = UXTO.getUnspentTransactionScript(self.script)
                    if unspentTransactionScript != None:
                        _output = unspentTransactionScript.output
                if _output != None:
                    result = self.handleLocalScript(fromAccount, _output, False)
            else:
                result = MemoryPool.addUnconfirmedTransaction(fromAccount, self.script, self.value, self.gasLimit, self.gasPrice, None, self.parameters)
                try:
                    result = DataType.toHex(result)
                except:
                    pass
        if result != None:
            callback(
                JSONRPC.createResultObject(result, self.id)
            )
        else:
            self.onFailure(callback)
    
    def handleLocalScript(self, fromAccount, output, deploy):
        gasLimit = Config.getIntValue('TRANSACTION_LOCAL_GAS_LIMIT')
        gasPrice = Config.getIntValue('TRANSACTION_LOCAL_GAS_PRICE')
        localTx = Transaction(gasLimit, gasPrice)
        localTx.gasRemaining = Config.getIntValue('TRANSACTION_LOCAL_GAS_REMAINING')
        _input = None
        if deploy:
            pass
        else:
            scriptData = []
            scriptData.append(DataType.zeroFillArray(0, 32))
            scriptData.append(DataType.zeroFillArray(0, 32))
            scriptData.append(fromAccount.address)
            scriptData.extend(self.parameters)

            _input = Input(Config.getValue('SCRIPT_TRANSACTION_ID'), Config.getIntValue('SCRIPT_OUTPUT_INDEX'))
            _input.witness = scriptData
        if RVM.run(localTx, _input, output, True, deploy, True):   
            if len(localTx.internalOutputs) > 0:
                internalOutput = localTx.internalOutputs[-1]
                if deploy:
                    PersistentStorage.add(internalOutput.address, internalOutput, True)
                    result = 'Script Deployed Locally'
                else:
                    result = internalOutput.script
                    try:
                        result = DataType.toHex(result)
                        result = DataType.asInt(result, 16)
                    except ValueError:
                        pass
                return result
        return None

    def logs(self, callback = None):
        logs = PersistentStorage.get(self.script, True)
        _logs = []
        for log in logs:
            _logs.append({
                'address': log.address,
                'data': log.data,
                'topics': log.topics
            })
        callback(
            JSONRPC.createResultObject(_logs, self.id)
        )
    
    def onFailure(self, callback = None):
        callback(
            JSONRPC.createErrorObject(-32011, 'invalid message', 'rejected script', self.id)
        )