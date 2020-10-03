from concurrent.futures import ThreadPoolExecutor
from recip.util import Config
from recip.util import DataType
from recip.util import RLP
from recip.util import Log
import socket

class Network:
    executor = ThreadPoolExecutor(max_workers=Config.getIntValue('MAX_OUTBOUND_PEER_CONNECTIONS'))
    executor._thread_name_prefix = 'OutboundConnection'

def sendData(host, data, hasPayload = True):
    future = Network.executor.submit(_sendData, host, data, hasPayload)
    return future.result()

def _sendData(host, data, hasPayload):
    try:
        if ':' in host:
            host = host.split(':')
            host[1] = DataType.asInt(host[1])
            host = tuple(host)
        else:
            host = (host, getSocketPort())
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(host)
            sock.settimeout(Config.getIntValue("CONNECTION_TIMEOUT"))
            data = DataType.serialize(data)
            dataLen = len(data)
            dataLen = DataType.intToBytes(dataLen, Config.getIntValue("SOCKET_HEADER_BUFFER_SIZE"))
            sock.sendall(dataLen)
            sock.sendall(data)
            if hasPayload:
                payload = getSocketPayload(sock)
                return RLP.decode(payload)
    except IOError:
        Log.error('Unable to send data to host: %s data: %s' % (host, data))
    return None

def sendDataByUDP(host, port, data):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.settimeout(Config.getIntValue("CONNECTION_TIMEOUT"))
            data = DataType.serialize(data)
            sock.sendto(data, (host, port))
            return sock.recvfrom(Config.getIntValue("SOCKET_RECEIVE_BUFFER_SIZE"))
    except IOError:
        Log.error('Unable to send data by UDP to host: %s port: %s data: %s' % (host, port, data))
    return None, None

def getSocketPayload(socket, bufferSize = Config.getIntValue("SOCKET_HEADER_BUFFER_SIZE")):
    payload = b''
    payloadLen = None
    hasData = True
    while hasData:
        data = socket.recv(bufferSize)
        if payloadLen == None:
            payloadLen = DataType.deserialize(data, DataType.INT, 0)
            bufferSize = Config.getIntValue("SOCKET_RECEIVE_BUFFER_SIZE")
        else:
            dataLen = len(data)
            if dataLen > 0:
                payload += data
                if dataLen >= payloadLen:
                    hasData = False
                else:
                    payloadLen -= dataLen
            else:
                hasData = False
    return payload
    
def getHostname(includePort = True):
    try:
        if Config.getBoolValue("REQUIRE_HOSTNAME"):
            hostname = socket.gethostname()
        else:
            hostname = getIpAddress(False)
        if includePort:
            hostname += "{0}{1}".format(':', getSocketPort())
        return hostname
    except IOError:
        Log.error('Unable to get hostname')
    return None

def getIpAddress(includePort = True):
    ipAddress = None
    try:
        hostname = socket.gethostname()
        ipAddress = socket.gethostbyname(hostname)
    except IOError:
        Log.error('Unable to get ip address')
    if ipAddress == None or ipAddress.startswith("127"):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            try:
                sock.connect(("8.8.8.8", 53))
                sockname = sock.getsockname()
                ipAddress = sockname[0]
            except IOError:
                Log.error('Unable to get ip address via fallback.')
    if includePort:
        ipAddress += "{0}{1}".format(':', getSocketPort())
    return ipAddress

def getSocketPort():
    return Config.getIntValue("SOCKET_PORT")

def setSocketPort(port):
    Config.setKeyValue("SOCKET_PORT", port)

def getNodeHostname():
    return Config.getValue("NODE_HOSTNAME")

def setNodeHostname(host):
    Config.setKeyValue("NODE_HOSTNAME", host)