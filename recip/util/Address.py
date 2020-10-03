from recip.util import DataType
from recip.util import Validator

def toAddressBytes(address):
    if address.startswith('0x'):
        address = address[2:]
    return DataType.fromHex(address)

def toAddressStr(addressBytes):
    return DataType.toHex(addressBytes)

def to0xAddress(addressBytes):
    address = toAddressStr(addressBytes)
    return "0x{0}".format(address)