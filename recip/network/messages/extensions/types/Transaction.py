from recip.network.messages.extensions.ExtMessage import ExtMessage
from recip.network.messages.extensions import ExtMessageType
from recip.storage import Accounts
from recip.storage import MemoryPool
from recip.util import Address
from recip.util import DataType
from recip.util import JSONRPC
from recip.util import Validator
from recip.util import Units

class Transaction(ExtMessage):
    def __init__(self):
        super().__init__()
        self.fromAddress = None
        self.toAddress = None # Multi Signature or standard
        self.value = None
        self.gasLimit = None
        self.gasPrice = None

        # Multi Signature
        self.threshold = None
        self.publicKeys = None
        self.signatures = None
    
    def validate(self):
        if not Validator.address(self.fromAddress):
            return False
        if self.isMultiSig():
            if self.isTxFromMultiSig():
                if self.publicKeys == None or len(self.publicKeys) == 0:
                    return False
                if self.signatures == None or len(self.signatures) == 0:
                    return False
                for publicKey in self.publicKeys:
                    if not Validator.public(publicKey):
                        return False
                for signature in self.signatures:
                    if not Validator.signature(signature):
                        return False
                if len(self.publicKeys) != len(self.signatures):
                    return False
            if self.threshold == None or self.threshold <= 0:
                return False
        if not Validator.address(self.toAddress):
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
            keys = None
            if self.isMultiSig():
                if self.isTxFromMultiSig():
                    keys = ['fromAddress', 'publicKeys', 'signatures', 'threshold', 'toAddress', 'value', 'gasLimit', 'gasPrice']
                else:
                    keys = ['fromAddress', 'threshold', 'toAddress', 'value', 'gasLimit', 'gasPrice']
            else:
                keys = ['fromAddress', 'toAddress', 'value', 'gasLimit', 'gasPrice']
            if self.validateParameters(keys):
                self.fromAddress = Address.toAddressBytes(self.params['fromAddress'])
                if self.isMultiSig():
                    if self.isTxFromMultiSig():
                        self.publicKeys = []
                        _publicKeys = self.params['publicKeys']
                        for publicKey in _publicKeys:
                            publicKey = DataType.fromHex(publicKey)
                            self.publicKeys.append(publicKey)
                        self.signatures = []
                        _signatures = self.params['signatures']
                        for signature in _signatures:
                            signature = DataType.fromHex(signature)
                            self.signatures.append(signature)
                    self.threshold = self.params['threshold']
                self.toAddress = Address.toAddressBytes(self.params['toAddress'])
                self.value = Units.toUnits(self.params['value'])
                self.gasLimit = self.params['gasLimit']
                self.gasPrice = Units.toUnits(self.params['gasPrice'])
                if self.validate():
                    return True
        return False

    def isMultiSig(self):
        if ExtMessageType.SEND_TRANSACTION_TO_MULTISIG == self.method:
            return True
        if ExtMessageType.SEND_TRANSACTION_FROM_MULTISIG == self.method:
            return True
        if ExtMessageType.SIGN_MULTISIG_OUTPUT == self.method:
            return True
        return False

    def isTxFromMultiSig(self):
        if ExtMessageType.SEND_TRANSACTION_FROM_MULTISIG == self.method:
            return True
        return False
    
    def onSuccess(self, callback = None):
        if ExtMessageType.SEND_TRANSACTION == self.method:
            self.addUnconfirmedTransaction(callback)
        elif ExtMessageType.SEND_TRANSACTION_TO_MULTISIG == self.method:
            self.addUnconfirmedTransaction(callback)
        elif ExtMessageType.SEND_TRANSACTION_FROM_MULTISIG == self.method:
            self.addUnconfirmedMultiSigTransaction(callback)
        elif ExtMessageType.SIGN_MULTISIG_OUTPUT == self.method:
            self.signMultiSigOutput(callback)
        else:
            self.onFailure(callback)

    def addUnconfirmedTransaction(self, callback = None):
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

    def addUnconfirmedMultiSigTransaction(self, callback = None):
        fromAccount = Accounts.getAccountByAddress(self.fromAddress)
        txId = None
        if fromAccount != None:
            txId = MemoryPool.addUnconfirmedMultiSigTransaction(fromAccount, self.publicKeys, self.signatures, self.toAddress, self.value, self.gasLimit, self.gasPrice, self.threshold)                
        if txId != None:
            callback(
                JSONRPC.createResultObject(DataType.toHex(txId), self.id)
            )
        else:
            self.onFailure(callback)

    def signMultiSigOutput(self, callback = None):
        signatures = []
        multiSigAccount = Accounts.getAccountByAddress(self.fromAddress)
        if multiSigAccount != None:
            transaction = MemoryPool.createUnconfirmedMultiSigTransaction(multiSigAccount, self.toAddress, self.value, self.gasLimit, self.gasPrice, self.threshold)
            if transaction != None:
                for txIn in transaction.inputs:
                    multiSigAddress = DataType.toHex(multiSigAccount.address)
                    _publicKeys = txIn.witness[::2]
                    _signatures = txIn.witness[1::2]
                    for publicKey, signature in zip(_publicKeys, _signatures):
                        publicKey = DataType.toHex(publicKey)
                        signature = DataType.toHex(signature)
                        signatures.append({
                            'address': multiSigAddress,
                            'public': publicKey,
                            'signature': signature
                        })
        callback(
            JSONRPC.createResultObject(signatures, self.id)
        )
    
    def onFailure(self, callback = None):
        callback(
            JSONRPC.createErrorObject(-32004, 'invalid message', 'rejected transaction', self.id)
        )