from recip.util.Serializable import Serializable
from recip.util import Address
from recip.util import Crypto
from recip.util import Validator

class Log(Serializable):
    def __init__(self, address = None, data = None, topics = None):
        self.address = address
        self.data = data
        self.topics = topics
    
    def serialize(self):
        return {
            self.address,
            self.data,
            self.topics
        }
    
    def deserialize(self, buffer):
        self.address = buffer[0]
        self.data = buffer[1]
        self.topics = buffer[2]