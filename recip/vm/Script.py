from recip.util import Config
from recip.util import DataType
from recip.vm import Opcodes

def verifySignature():
    script = bytearray()
    
    script.append(Config.getIntValue("SCRIPT_VERSION"))
    script.append(Opcodes.alias('DUP1'))
    script.append(Opcodes.alias('PUBADDR', True))
    script.append(Opcodes.alias('ADDRESS'))
    script.append(Opcodes.alias('EQ'))
    script.append(Opcodes.alias('VERIFY', True))
    script.append(Opcodes.alias('CHECKSIGVERIFY', True))

    return DataType.serialize(script)

def verifyMultiSignature():
    script = bytearray()
    
    script.append(Config.getIntValue("SCRIPT_VERSION"))
    script.append(Opcodes.alias('CHECKMULTISIGVERIFY', True))

    return DataType.serialize(script)

def verifyAtomicSwapSignature():
    script = bytearray()
    
    script.append(Config.getIntValue("SCRIPT_VERSION"))
    script.append(Opcodes.alias('CHECKATOMICSWAPVERIFY', True))

    return DataType.serialize(script)

def verifyAtomicSwapLock():
    script = bytearray()
    
    script.append(Config.getIntValue("SCRIPT_VERSION"))
    script.append(Opcodes.alias('CHECKATOMICSWAPLOCKVERIFY', True))

    return DataType.serialize(script)

def merge():
    script = bytearray()
    
    script.append(Config.getIntValue("SCRIPT_VERSION"))
    script.append(Opcodes.alias('MERGE', True))
    
    return DataType.serialize(script)