from recip.core import AccountType
from recip.util.Serializable import Serializable
from recip.util import Address
from recip.util import Crypto
from recip.util import DataType
from recip.util import Validator

class Account(Serializable):
    def __init__(self, address = None, public = None, private = None, type=AccountType.STANDARD):
        if address == None and public == None and private == None:
            address, public, private = Crypto.generateKeys()
        self.address = address
        self.public = public
        self.private = private
        self.type = type

    def __key(self):
        return (self.address)
    
    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if other == None:
            return self.__key() == other
        return self.__key() == other.__key()
        
    def validate(self):
        if not Validator.address(self.address):
            return False
        if not Validator.public(self.public):
            return False
        if not Validator.private(self.private):
            return False
        if type == None or len(type) == 0:
            return False
        return True

    def isMultiSig(self):
        if self.type == AccountType.MULTISIGNATURE:
            return True
        return False

    def sign(self, message):
        return Crypto.sign(self.private, message)
        
    def verify(self, signature, message):
        return Crypto.verify(self.public, signature, message)
    
    def serialize(self):
        return {
            'address': Address.toAddressStr(self.address),
            'public': DataType.toHex(self.public),
            'private': DataType.toHex(self.private),
            'type': self.type
        }
    
    def deserialize(self, buffer):
        self.address = Address.toAddressBytes(buffer['address'])
        self.public = DataType.fromHex(buffer['public'])
        self.private = DataType.fromHex(buffer['private'])
        self.type = buffer['type']