from recip.util.Serializable import Serializable
from distutils.util import strtobool
from decimal import Decimal
from struct import pack, unpack
from recip.util import Config
from time import time
import math

INT = 'INT'
BOOL = 'BOOL'
DECIMAL = 'DECIMAL'
STRING = 'STRING'
BYTES = 'BYTES'
LIST = 'LIST'

def serialize(data):
    if data is None:
        return b''
    elif isinstance(data, int):
        return intToBytes(data)
    elif isinstance(data, bool):
        return pack('?', data) 
    elif isinstance(data, Decimal):
        return pack('>d', data)
    elif isinstance(data, str):
        return bytes(data, encoding=Config.getValue("ENCODING"))
    elif isinstance(data, bytearray):
        return bytes(data)
    elif isinstance(data, Serializable):
        return data.serialize()
    return data

def deserialize(dataBytes, dataType = STRING, defaultValue = None):
    if dataBytes != None and len(dataBytes) > 0:
        if dataType == INT:
            return bytesToInt(dataBytes)
        elif dataType == BOOL:
            return unpack('?', dataBytes)[0]
        elif dataType == DECIMAL:
            value = unpack('>d', dataBytes)[0]
            return asDecimal(value)
        elif dataType == STRING:
            return dataBytes.decode(Config.getValue("ENCODING"))
        elif dataType == LIST:
            data = []
            for dataByte in dataBytes:
                data.append(deserialize(dataByte))
            return data
    if dataType == DECIMAL:
        return asDecimal(defaultValue)
    else:
        return defaultValue

def intToBytes(value, bytesLen = None):
    if isinstance(value, bytes):
        return value
    if bytesLen == None:
        bytesLen = math.ceil(value.bit_length() / Config.getIntValue("BITS_PER_BYTE"))
    if bytesLen <= 0:
        bytesLen = 1
    return value.to_bytes(bytesLen, byteorder=Config.getValue("BYTE_ORDER"))

def bytesToInt(numberBytes):
    if isinstance(numberBytes, int):
        return numberBytes
    return int.from_bytes(numberBytes, byteorder=Config.getValue("BYTE_ORDER"))

def zeroFillArray(item, length, left=True):
    if isinstance(item, int):
        item = intToBytes(item, length)
    elif isinstance(item, bytes) and len(item) < length:
        fillLen = length - len(item)
        fill = b'\x00' * fillLen
        if left:
            item = fill + item 
        else:
            item = item + fill
    return item

def fromHex(data):
    dataBytes = None
    if data == None:
        dataBytes = b''
    elif isinstance(data, list):
        dataBytes = []
        for value in data:
            dataBytes.append(_fromHex(value))
    else:
        dataBytes = _fromHex(data)
    return dataBytes

def _fromHex(data):
    if data.startswith('0x'):
        data = data[2:]
    data = bytearray.fromhex(data)
    return serialize(data)

def toHex(dataBytes):
    data = None
    if dataBytes == None:
        data = ''
    elif isinstance(dataBytes, list):
        data = []
        for dataByte in dataBytes:
            data.append(_toHex(dataByte))
    else:
        data = _toHex(dataBytes)
    return data

def _toHex(dataBytes):
    data = []
    for dataByte in dataBytes:
        data.append('{0:0{1}x}'.format(dataByte, 2))
    return ''.join(data)

def asTime():
    return asInt(round(time() * 1000))

def asString(value):
    if isinstance(value, str):
        return value
    return str(value)

def asInt(value, base=10):
    if isinstance(value, int):
        return value
    return int(value, base)

def asBool(value):
    if isinstance(value, bool):
        return value
    return bool(strtobool(value))

def asDecimal(value):
    if isinstance(value, Decimal):
        return value
    return Decimal(value)

def asFloat(value):
    if isinstance(value, float):
        return value
    return float(value)
