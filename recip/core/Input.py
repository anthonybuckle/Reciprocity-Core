from recip.core.Outpoint import Outpoint
from recip.util.Serializable import Serializable
from recip.util import Config
from recip.util import RLP

class Input(Serializable):
    def __init__(self, txId = None, outputIndex = None, witness = None):
        self.outpoint = Outpoint(txId, outputIndex)
        self.witness = witness
    
    def isCoinbase(self):
        if self.outpoint.txId != Config.getBytesValue('COINBASE_TRANSACTION_ID', False):
            return False
        if self.outpoint.outputIndex != Config.getIntValue('COINBASE_OUTPUT_INDEX'):
            return False
        return True 
        
    def initWitness(self, signature, public):
        if self.witness == None:
            self.witness = []
            self.witness.append(signature)
            self.witness.append(public)
        else:
            self.witness.insert(0, public)
            self.witness.insert(0, signature)

    def serialize(self):
        item = [
            self.outpoint
        ]
        return RLP.encode(item)
    
    def deserialize(self, buffer):
        decodedBuffer = RLP.decode(buffer)
        self.outpoint = Outpoint()
        self.outpoint.deserialize(decodedBuffer[0])
