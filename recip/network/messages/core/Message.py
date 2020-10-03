from abc import ABC, abstractmethod
from recip.util import Network
 
class Message(ABC):
    def __init__(self):
        self.addrRecv = None
        self.addrFrom = Network.getHostname()
    
    def validatePayload(self, payload, length):
        if payload == None:
            return False
        if len(payload) != length:
            return False
        return True
    
    @abstractmethod
    def validate(self):
        raise NotImplementedError("Missing validate method")
    
    @abstractmethod
    def send(self):
        raise NotImplementedError("Missing send method")
    
    @abstractmethod
    def sendFailure(self, message):
        raise NotImplementedError("Missing sendFailure method")
    
    @abstractmethod
    def onSuccess(self, callback = None):
        raise NotImplementedError("Missing onSuccess method")
    
    @abstractmethod
    def onFailure(self, callback = None):
        raise NotImplementedError("Missing onFailure method")
    
    @abstractmethod
    def serialize(self):
        raise NotImplementedError("Missing serialize method")
    
    @abstractmethod
    def deserialize(self, payload):
        raise NotImplementedError("Missing deserialize method")