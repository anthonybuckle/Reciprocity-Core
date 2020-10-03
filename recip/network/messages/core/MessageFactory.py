from recip.network.messages.core.types.Addr import Addr
from recip.network.messages.core.types.Block import Block
from recip.network.messages.core.types.GetAddr import GetAddr
from recip.network.messages.core.types.GetBlocks import GetBlocks
from recip.network.messages.core.types.GetData import GetData
from recip.network.messages.core.types.Inv import Inv
from recip.network.messages.core.types.MemPool import MemPool
from recip.network.messages.core.types.Ping import Ping
from recip.network.messages.core.types.Pong import Pong
from recip.network.messages.core.types.Tx import Tx
from recip.network.messages.core.types.VerAck import VerAck
from recip.network.messages.core.types.Version import Version
from recip.network.messages.core import MessageType
from recip.util import DataType

def getInstance(msg):
    msgType = msg
    if isinstance(msg, list):
        msgType = DataType.deserialize(msg[0])
        
    '''Socket Messages Types'''
    if MessageType.ADDR == msgType:
        return Addr()
    elif MessageType.BLOCK == msgType:
        return Block()
    elif MessageType.GETADDR == msgType:
        return GetAddr()
    elif MessageType.GETBLOCKS == msgType:
        return GetBlocks()
    elif MessageType.GETDATA == msgType:
        return GetData()
    elif MessageType.INV == msgType:
        return Inv()
    elif MessageType.MEMPOOL == msgType:
        return MemPool()
    elif MessageType.PING == msgType:
        return Ping()
    elif MessageType.PONG == msgType:
        return Pong()
    elif MessageType.TX == msgType:
        return Tx()
    elif MessageType.VERACK == msgType:
        return VerAck()
    elif MessageType.VERSION == msgType:
        return Version()