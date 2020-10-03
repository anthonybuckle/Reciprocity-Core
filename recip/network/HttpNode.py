from recip.network.messages.extensions import ExtMessageFactory
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from threading import Thread
from recip.util import DataType
from recip.util import Config
from recip.util import Http
from recip.util import JSONRPC
import socket
import json
import ssl
class HttpNode:
    def __init__(self, port):
        self.port = port
        
        def handler(*args):
            HttpNodeRequestHandler(*args)
            
        self.node = HttpNodeServer((Config.getValue("NODE_HOSTNAME"), port), handler)
        
    def start(self):
        httpNodeThread = Thread(name='HttpNode', target=self.node.serve_forever)
        httpNodeThread.start()
        
    def shutdown(self):
        self.node.shutdown()

'''
    ThreadingHTTPServer requires python 3.7 or above.
'''
class HttpNodeServer(HTTPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if Config.getBoolValue("HTTP_SSL_ENABLE"):
            self.socket = ssl.wrap_socket(self.socket, certfile=Config.getValue("HTTP_SSL_CERTIFICATE"), server_side=True)
        self.socket.bind(self.server_address)
    
class HttpNodeRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args):
        BaseHTTPRequestHandler.__init__(self, *args)
    
    def do_HEAD(self, contentType):
        self.send_response(200)
        self.send_header('Content-type', contentType)
        self.end_headers()
    
    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Reciprocity"')
        self.send_header('Content-type', 'application/json')
        self.end_headers()
    
    def hasAuthorization(self):
        if Config.getBoolValue("HTTP_RPC_AUTHENTICATION_ENABLE"):
            authorizationHeader = self.headers.get('Authorization')
            if authorizationHeader == None:
                return False
            elif authorizationHeader != Http.getBasicAuth():
                return False
        return True
    
    def do_GET(self):
        if self.hasAuthorization():
            response = JSONRPC.createErrorObject(-32601, 'not found', 'method not found', None)
            self.writeResponse(response, doHead = True)
        else:
            response = JSONRPC.createErrorObject(-32010, 'unauthorized', 'you are not authorized to access this resource', None)
            self.writeResponse(response, doHead = False)
    
    def do_POST(self):
        if self.hasAuthorization():  
            length = DataType.asInt(self.headers['Content-Length'])
            payload = self.rfile.read(length)
            payload = DataType.deserialize(payload)
            payload = json.loads(payload)
            self.handlePayload(payload)
        else:
            response = JSONRPC.createErrorObject(-32010, 'unauthorized', 'you are not authorized to access this resource', None)
            self.writeResponse(response, doHead = False)

    def handlePayload(self, payload):
        message = ExtMessageFactory.getInstance(payload)
        if message.deserialize(payload):
            message.onSuccess(self.writeResponse)
        else:
            message.onFailure(self.writeResponse)
    
    def writeResponse(self, response, contentType = 'application/json', doHead = True):
        if doHead:
            self.do_HEAD(contentType)
        else:
            self.do_AUTHHEAD()
        if contentType == "application/json":
            response = json.dumps(response, sort_keys=False)
            response = DataType.serialize(response)
        self.wfile.write(response)