from concurrent.futures import ThreadPoolExecutor
from recip.network.messages.core import MessageFactory
from socketserver import BaseRequestHandler
from recip.network.SyncManager import SyncManager
from socketserver import TCPServer
from recip.util import Config, DataType, RLP, Network
import socket

class SocketNode:
    def __init__(self, port):
        self.port = port
        
        def handler(*args):
            SocketNodeRequestHandler(*args)
            
        self.node = SocketNodeServer((Config.getValue("NODE_HOSTNAME"), port), handler)
        
    def start(self):
        self.node.serve_forever()
        
    def shutdown(self):
        self.node.shutdown()
        
    def sync(self):
        syncManager = SyncManager()
        syncManager.start()
        
class SocketNodeServer(TCPServer):
    executor = ThreadPoolExecutor(max_workers=Config.getIntValue('MAX_INBOUND_PEER_CONNECTIONS'))
    executor._thread_name_prefix = 'InboundConnection'

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

    def process_request(self, request, client_address):
        SocketNodeServer.executor.submit(super().process_request, request, client_address)

class SocketNodeRequestHandler(BaseRequestHandler):
    def __init__(self, *args):
        BaseRequestHandler.__init__(self, *args)
    
    def getAddrRecv(self):
        addrRecv = self.request.getsockname()
        return "{0}{1}{2}".format(addrRecv[0], ':', Network.getSocketPort())
    
    def getAddrFrom(self):
        addrFrom = self.request.getpeername()
        return "{0}{1}{2}".format(addrFrom[0], ':', Network.getSocketPort())
    
    def handle(self):
        payload = Network.getSocketPayload(self.request)        
        payload = RLP.decode(payload)
        self.handlePayload(payload)
        
    def handlePayload(self, payload):
        message = MessageFactory.getInstance(payload)
        message.addrRecv = self.getAddrRecv()
        message.addrFrom = self.getAddrFrom()
        if message.deserialize(payload):
            message.onSuccess(self.writeResponse)
        else:
            message.onFailure(self.writeResponse)
    
    def writeResponse(self, response):
        response = DataType.serialize(response)
        responseLen = len(response)
        responseLen = DataType.intToBytes(responseLen, Config.getIntValue("SOCKET_HEADER_BUFFER_SIZE"))
        self.request.sendall(responseLen)
        self.request.sendall(response)