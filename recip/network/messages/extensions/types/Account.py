from recip.network.messages.extensions.ExtMessage import ExtMessage
from recip.network.messages.extensions import ExtMessageType
from recip.core.Account import Account as CoreAccount
from recip.core import AccountType
from recip.storage import Accounts
from recip.util import Address
from recip.util import Crypto
from recip.util import DataType
from recip.util import JSONRPC
from recip.util import Validator
from recip.util import Units

class Account(ExtMessage):
    def __init__(self):
        super().__init__()
        self.publicKeys = []
        self.address = []
    
    def validate(self):
        if self.address == None or self.publicKeys == None:
            return False
        for publicKey in self.publicKeys:
            if not Validator.public(publicKey):
                return False
        for addr in self.address:
            if not Validator.address(addr):
                return False
        return True
    
    def deserialize(self, payload):
        if self.validatePayload(payload):
            self.deserializePayload(payload)
            if self.validateParameters():
                if self.isMultiSig():
                    for publicKey in self.params:
                        publicKey = DataType.fromHex(publicKey)
                        self.publicKeys.append(publicKey)
                else:                
                    for addr in self.params:
                        addr = Address.toAddressBytes(addr)
                        self.address.append(addr)
                if self.validate():
                    return True
        return False
    
    def onSuccess(self, callback = None):
        if ExtMessageType.CREATE_ATOMIC_SWAP_ACCOUNT == self.method:
            self.createAtomicSwapAccount(callback)
        elif ExtMessageType.CREATE_MULTISIG_ACCOUNT == self.method:
            self.createMultiSigAccount(callback)
        elif ExtMessageType.GET_ACCOUNTS == self.method:
            self.get(callback)
        elif ExtMessageType.GET_NEW_ACCOUNT == self.method:
            self.add(callback)
        elif ExtMessageType.DELETE_ACCOUNTS == self.method:
            self.remove(callback)
        else:
            self.onFailure(callback)

    def isMultiSig(self):
        if ExtMessageType.CREATE_MULTISIG_ACCOUNT == self.method:
            return True
        if ExtMessageType.CREATE_ATOMIC_SWAP_ACCOUNT == self.method:
            return True
        return False

    def createAtomicSwapAccount(self, callback = None):
        _address, _public, _private = Crypto.generateKeys()
        privateBytes = bytearray()
        privateBytes.extend(_address)
        privateBytes.extend(_public)
        privateBytes.extend(_private)
        privateKey = Crypto.generateHash(privateBytes)
        self.createNewMultiSigAccountType(AccountType.ATOMIC_SWAP, privateKey, callback)

    def createMultiSigAccount(self, callback = None):
        self.createNewMultiSigAccountType(AccountType.MULTISIGNATURE, None, callback)

    def createNewMultiSigAccountType(self, accountType, privateKey, callback = None):
        multiSigAddressBytes = bytearray()
        for publicKey in self.publicKeys:
            multiSigAddressBytes.extend(publicKey)
        multiSigAddress = Crypto.generateAddress(multiSigAddressBytes)
        account = CoreAccount(multiSigAddress, self.publicKeys, privateKey, accountType)
        Accounts.addAccount(account)
        multiSigAddress = Address.to0xAddress(multiSigAddress)
        callback(
            JSONRPC.createResultObject(multiSigAddress, self.id)
        )

    def get(self, callback = None):
        accounts = []
        # Account Types
        standard = []
        multisig = []
        atomicswap = []
        for account in Accounts.getAccounts():
            confirmedBalance = Accounts.getConfirmedBalanceByAddress(account.address)
            confirmedBalance = Units.toValue(confirmedBalance)
            confirmedBalance = DataType.asFloat(confirmedBalance)
            address = Address.to0xAddress(account.address)
            accountInfo = {
                'address': address,
                'type': account.type,
                'balance': confirmedBalance
            }
            if account.type == AccountType.STANDARD:
                standard.append(accountInfo)
            elif account.type == AccountType.MULTISIGNATURE:
                multisig.append(accountInfo)
            elif account.type == AccountType.ATOMIC_SWAP:
                atomicswap.append(accountInfo)
        accounts.extend(standard)
        accounts.extend(multisig)
        accounts.extend(atomicswap)
        callback(
            JSONRPC.createResultObject(accounts, self.id)
        )
        
    def add(self, callback = None):
        account = CoreAccount()
        Accounts.addAccount(account)
        address = Address.to0xAddress(account.address)
        callback(
            JSONRPC.createResultObject(address, self.id)
        )
    
    def remove(self, callback = None):
        removed = False
        for addr in self.address:
            removed = Accounts.removeAccount(addr)
            if not removed:
                break
        if removed:
            callback(
                JSONRPC.createResultObject('accounts removed', self.id)
            )
        else:
            callback(
                JSONRPC.createErrorObject(-32003, 'delete failed', 'failed to remove accounts', self.id)
            )
    
    def onFailure(self, callback = None):
        callback(
            JSONRPC.createErrorObject(-32000, 'invalid message', 'invalid account request', self.id)
        )
