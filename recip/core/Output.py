from recip.util.Serializable import Serializable
from recip.vm import Opcodes
from recip.util import Config
from recip.util import DataType
from recip.util import RLP

class Output(Serializable):
    def __init__(self, address = None, script = None, value = None, extraData = None):
        self.address = address
        self.script = script
        self.value = value
        self.extraData = extraData

        self.store = True

    def hasExtScript(self):
        if self.script[0] == Config.getIntValue("EXTENSION_SCRIPT_VERSION"):
            return True
        else:
            return False

    def isMultiSig(self):
        if len(self.script) != Config.getIntValue('SCRIPT_MULTISIG_LEN'):
            return False
        if self.script[0] != Config.getIntValue('SCRIPT_VERSION', False):
            return False
        if self.script[1] != Opcodes.alias('CHECKMULTISIGVERIFY', True):
            return False
        return True

    def isAtomicSwap(self):
        if len(self.script) != Config.getIntValue('SCRIPT_ATOMIC_SWAP_LEN'):
            return False
        if self.script[0] != Config.getIntValue('SCRIPT_VERSION', False):
            return False
        if self.script[1] != Opcodes.alias('CHECKATOMICSWAPVERIFY', True):
            return False
        return True

    def isAtomicLock(self):
        if len(self.script) != Config.getIntValue('SCRIPT_ATOMIC_SWAP_LEN'):
            return False
        if self.script[0] != Config.getIntValue('SCRIPT_VERSION', False):
            return False
        if self.script[1] != Opcodes.alias('CHECKATOMICSWAPLOCKVERIFY', True):
            return False
        return True

    def serialize(self):
        item = [
            self.address,
            self.script,
            self.value,
            self.extraData
        ]
        return RLP.encode(item)
    
    def deserialize(self, buffer):
        decodedBuffer = RLP.decode(buffer)
        self.address = decodedBuffer[0]
        self.script = decodedBuffer[1]
        self.value = DataType.deserialize(decodedBuffer[2], DataType.INT, 0)
        self.extraData = decodedBuffer[3]
            