from abc import ABC, abstractmethod
 
class Serializable(ABC):
    
    @abstractmethod
    def serialize(self):
        raise NotImplementedError("Missing serialize method")
    
    @abstractmethod
    def deserialize(self, buffer):
        raise NotImplementedError("Missing deserialize method")