from recip.util.Serializable import Serializable
from recip.util import Address
from recip.util import Crypto
from recip.util import Validator

class Sidechain(Serializable):
    def __init__(self, address = None):
        self.address = address
        
    def validate(self):
        if not Validator.address(self.address):
            return False
        return True

    def __key(self):
        return (self.address)
    
    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if other == None:
            return self.__key() == other
        return self.__key() == other.__key()
    
    def serialize(self):
        return {
            'address': Address.toAddressStr(self.address)
        }
    
    def deserialize(self, buffer):
        self.address = Address.toAddressBytes(buffer['address'])