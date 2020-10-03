from recip.util import DataType

SHORT_PAYLOAD       = 0x37

BYTE_PREFIX_START   = 0x00
BYTE_PREFIX_END     = 0x7f
STRING_PREFIX_START = 0x80
STRING_PREFIX_END   = 0xbf
LIST_PREFIX_START   = 0xc0
LIST_PREFIX_END     = 0xff

STRING_55_LEN_MAX_RANGE = 0xb7
LIST_55_LEN_MAX_RANGE = 0xf7

def encode(item):
    item = DataType.serialize(item)
    encodedItem = b''
    if len(item) > 0:
        if isinstance(item, bytes):
            itemLen = len(item)
            if itemLen == 1 and item[0] <= BYTE_PREFIX_END:
                encodedItem += item
            else:
                encodedItem += encodeItem(item, itemLen, STRING_PREFIX_START)
        elif isinstance(item, list):
            for i in item:
                encodedItem += encode(i)
            itemLen = len(encodedItem)
            encodedItem = encodeItem(encodedItem, itemLen, LIST_PREFIX_START)
    else:
        if isinstance(item, bytes):
            encodedItem += DataType.intToBytes(STRING_PREFIX_START)
        elif isinstance(item, list):
            encodedItem += DataType.intToBytes(LIST_PREFIX_START)
    return encodedItem

def encodeItem(item, itemLen, prefix):
    if itemLen <= SHORT_PAYLOAD:
        return DataType.intToBytes(prefix + itemLen) + item
    else:
        itemLen = DataType.intToBytes(itemLen)
        return DataType.intToBytes(prefix + len(itemLen) + SHORT_PAYLOAD) + itemLen + item

def decode(buffer):
    decodedBuffer = b''
    if len(buffer) > 0:
        prefix = buffer[0]
        if prefix >= BYTE_PREFIX_START and prefix <= BYTE_PREFIX_END:
            decodedBuffer += DataType.intToBytes(prefix)
        elif prefix >= STRING_PREFIX_START and prefix <= STRING_PREFIX_END:
            offset = 1
            decodedBufferLen = None
            if prefix > STRING_55_LEN_MAX_RANGE:
                prefixLen = prefix - STRING_55_LEN_MAX_RANGE
                bufferLen = buffer[offset:offset + prefixLen]
                decodedBufferLen = DataType.bytesToInt(bufferLen)
                offset += prefixLen
            else:
                decodedBufferLen = prefix - STRING_PREFIX_START
            decodedBuffer += buffer[offset:offset + decodedBufferLen]
        elif prefix >= LIST_PREFIX_START and prefix <= LIST_PREFIX_END:
            decodedBuffer = []
            offset = 1
            decodedBufferLen = None
            if prefix > LIST_55_LEN_MAX_RANGE:
                prefixLen = prefix - LIST_55_LEN_MAX_RANGE
                bufferLen = buffer[offset:offset + prefixLen]
                decodedBufferLen = DataType.bytesToInt(bufferLen)
                offset += prefixLen
            else:
                decodedBufferLen = prefix - LIST_PREFIX_START
            buffer = buffer[offset:offset + decodedBufferLen]
            while len(buffer) > 0:
                tempBufferDecoded = decode(buffer)
                decodedBuffer.append(tempBufferDecoded)
                offset = 1
                prefix = buffer[0]
                if prefix >= BYTE_PREFIX_START and prefix <= BYTE_PREFIX_END:
                    decodedBufferLen = 0
                elif prefix >= STRING_PREFIX_START and prefix <= STRING_PREFIX_END:
                    if prefix > STRING_55_LEN_MAX_RANGE:
                        prefixLen = prefix - STRING_55_LEN_MAX_RANGE
                        bufferLen = buffer[offset:offset + prefixLen]
                        decodedBufferLen = DataType.bytesToInt(bufferLen)
                        offset += prefixLen
                    else:
                        decodedBufferLen = prefix - STRING_PREFIX_START
                elif prefix >= LIST_PREFIX_START and prefix <= LIST_PREFIX_END:
                    if prefix > LIST_55_LEN_MAX_RANGE:
                        prefixLen = prefix - LIST_55_LEN_MAX_RANGE
                        bufferLen = buffer[offset:offset + prefixLen]
                        decodedBufferLen = DataType.bytesToInt(bufferLen) 
                        offset += prefixLen
                    else:
                        decodedBufferLen = prefix - LIST_PREFIX_START
                buffer = buffer[offset + decodedBufferLen:]
    return decodedBuffer