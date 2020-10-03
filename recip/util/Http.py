from urllib.request import Request, urlopen
from base64 import b64encode
from recip.util import Config
from recip.util import DataType
from recip.util import Log
    
def send(url, data = None, doBasicAuth = False, headers = None):
    try:
        if not url.startswith("http"):
            url = "http://" + url
        if data != None:
            data = DataType.serialize(data)
        httpHeaders = {}
        if doBasicAuth:
            httpHeaders.update({'Authorization': getBasicAuth()})
        if headers != None:
            httpHeaders.update(headers)
        req = Request(url, data, httpHeaders)
        response = urlopen(req, timeout=Config.getIntValue("CONNECTION_TIMEOUT"))
        return response.read()
    except IOError:
        Log.error('Unable to send request to url: %s' % url)
    return None 

def getBasicAuth():
    username = Config.getValue("HTTP_RPC_USERNAME")
    password = Config.getValue("HTTP_RPC_PASSWORD")
    userpass = "%s:%s" % (username, password)
    userpassBytes = DataType.serialize(userpass)
    userpassB64 = b64encode(userpassBytes)
    return 'Basic %s' % userpassB64.decode("ascii")
    
def getHttpPort():
    return Config.getIntValue("HTTP_PORT")

def setHttpPort(port):
    Config.setKeyValue("HTTP_PORT", port)

def getNodeHostname():
    return Config.getValue("NODE_HOSTNAME")

def setNodeHostname(host):
    Config.setKeyValue("NODE_HOSTNAME", host)