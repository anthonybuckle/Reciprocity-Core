from recip.network.messages.extensions.ExtMessage import ExtMessage
from recip.network.messages.extensions import ExtMessageType
from recip.core.Transaction import Transaction
from recip.storage import Accounts
from recip.storage import MemoryPool
from recip.util import Address
from recip.util import Config
from recip.util import Crypto
from recip.util import DataType
from recip.util import JSONRPC
from recip.util import Validator
from recip.util import Units
from recip.vm import Script

class AtomicSwap(ExtMessage):
    def __init__(self):
        super().__init__()
        self.fromAddress = None
        self.threshold = None
        self.toAddress = None
        self.value = None
        self.gasLimit = None
        self.gasPrice = None

        self.unsignedTx = None

    def validate(self):
        if self.isSignAtomicSwapTx():
            if self.unsignedTx == None or len(self.unsignedTx) == 0:
                return False
        else:
            if not Validator.address(self.fromAddress):
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
            if self.isSignAtomicSwapTx():
                keys = []
            else:
                keys = ['fromAddress', 'threshold', 'toAddress', 'value', 'gasLimit', 'gasPrice']
            if self.validateParameters(keys):
                if self.isSignAtomicSwapTx():
                    self.unsignedTx = self.params
                else:
                    self.fromAddress = Address.toAddressBytes(self.params['fromAddress'])
                    self.threshold = self.params['threshold']
                    self.toAddress = Address.toAddressBytes(self.params['toAddress'])
                    self.value = Units.toUnits(self.params['value'])
                    self.gasLimit = self.params['gasLimit']
                    self.gasPrice = Units.toUnits(self.params['gasPrice'])
                if self.validate():
                    return True
        return False
    
    def onSuccess(self, callback = None):
        if ExtMessageType.CREATE_ATOMIC_SWAP_TX == self.method:
            self.createAtomicSwapTx(callback)
        elif ExtMessageType.SEND_ATOMIC_SWAP_TX == self.method:
            self.sendAtomicSwapTx(callback)
        elif ExtMessageType.SIGN_ATOMIC_SWAP_TX == self.method:
            self.signAtomicSwapTx(callback)
        else:
            self.onFailure(callback)

    def isSignAtomicSwapTx(self):
        if ExtMessageType.SIGN_ATOMIC_SWAP_TX == self.method:
            return True
        return False

    def createAtomicSwapTx(self, callback):
        fromAccount = Accounts.getAccountByAddress(self.fromAddress)
        toMultiSigAccount = Accounts.getAccountByAddress(self.toAddress)

        '''
            A picks a random number x
        '''
        hashPrivKey = Crypto.generateHash(toMultiSigAccount.private)

        '''
            A creates TX1: "Pay w BTC to <B's public key> if (x for H(x) known and signed by B) or (signed by A & B)"
        '''
        transactionA1 = MemoryPool.createUnconfirmedAtomicSwapTransaction(fromAccount, toMultiSigAccount.address, self.value, self.gasLimit, self.gasPrice, Script.verifyAtomicSwapSignature(), self.threshold)

        if transactionA1 != None:
            '''
                A creates TX2: "Pay w BTC from TX1 to <A's public key>, locked 48 hours in the future, signed by A"
            '''
            transactionA2 = MemoryPool.createUnconfirmedAtomicSwapTransaction(fromAccount, toMultiSigAccount.address, self.value, self.gasLimit, self.gasPrice, Script.verifyAtomicSwapLock())
            if transactionA2 != None:
                tx = transactionA1.serialize()
                unsignedTx = transactionA2.serialize()
                result = {
                    'tx': DataType.toHex(tx),
                    'unsignedTx': DataType.toHex(unsignedTx)
                }
                callback(
                    JSONRPC.createResultObject(result, self.id)
                )
            else:
                self.onFailure(callback)
        else:
            self.onFailure(callback)

    def sendAtomicSwapTx(self, callback):
        transaction = None
        if MemoryPool.addSignedTransaction(transaction):
            callback(
                JSONRPC.createResultObject(result, self.id)
            )
        else:
            self.onFailure(callback)

    def signAtomicSwapTx(self, callback):
        transaction = Transaction()
        transaction.deserialize(self.unsignedTx)
        transaction.sign()
        if MemoryPool.addSignedTransaction(transaction):
            txId = transaction.hash()
            callback(
                JSONRPC.createResultObject(DataType.toHex(txId), self.id)
            )
        else:
            self.onFailure(callback)

    def onFailure(self, callback = None):
        callback(
            JSONRPC.createErrorObject(-32004, 'invalid message', 'rejected atomic swap', self.id)
        )