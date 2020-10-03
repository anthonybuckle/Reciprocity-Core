from abc import ABC, abstractmethod
from recip.util import JSONRPC
 
class ExtMessage(ABC):
    def __init__(self):
        self.jsonrpc = None
        self.method = None
        self.params = None
        self.id = None
    
    def validatePayload(self, payload):
        if payload == None:
            return False
        keys = JSONRPC.METHOD_OBJECT_KEYS
        for key in keys:
            if key not in payload:
                return False
        if payload['jsonrpc'] != JSONRPC.VERSION:
            return False
        if payload['id'] == None:
            return False
        return True
    
    def validateParameters(self, keys = []):
        if self.params == None:
            return False
        for key in keys:
            if key not in self.params:
                return False
        return True
    
    def deserializePayload(self, payload):
        self.jsonrpc = payload['jsonrpc']
        self.method = payload['method']
        self.params = payload['params']
        self.id = payload['id']
    
    @abstractmethod
    def validate(self):
        raise NotImplementedError("Missing validate method")
    
    @abstractmethod
    def deserialize(self, payload):
        raise NotImplementedError("Missing deserialize method")
    
    @abstractmethod
    def onSuccess(self, callback = None):
        raise NotImplementedError("Missing onSuccess method")
    
    @abstractmethod
    def onFailure(self, callback = None):
        raise NotImplementedError("Missing onFailure method")