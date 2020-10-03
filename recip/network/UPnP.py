import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from recip.util import Config
from recip.util import DataType
from recip.util import Network
from recip.util import Http

M_SEARCH_HOST = b'239.255.255.250'
M_SEARCH_PORT = 1900
M_SEARCH_ST   = b'urn:schemas-upnp-org:device:InternetGatewayDevice:1'
M_SEARCH_MAN  = b'ssdp:discover'
M_SEARCH_MX   = 3
M_SEARCH_ESCAPE = '\\r\\n'
M_SEARCH_QUERY = b'M-SEARCH * HTTP/1.1\r\nHost:%s:%d\r\nST:%s\r\nMan:"%s"\r\nMX:%d\r\n\r\n' % (M_SEARCH_HOST, 
                                                                                               M_SEARCH_PORT, 
                                                                                               M_SEARCH_ST, 
                                                                                               M_SEARCH_MAN, 
                                                                                               M_SEARCH_MX)

INTERNET_GATEWAY_DEVICE_LOCATIONS = {}
INTERNET_GATEWAY_DEVICES = []

def init():
    discoverInternetGatewayDevices()
    processIGDLocations()

def xmlFindText(xml, tag):
    if xml != None:
        root = ET.fromstring(xml)
        return root.findtext('.//' + tag)
    return None

def discoverInternetGatewayDevices():
    payload, addr = Network.sendDataByUDP(M_SEARCH_HOST, M_SEARCH_PORT, M_SEARCH_QUERY)
    payload = DataType.asString(payload)
    for data in payload.split(M_SEARCH_ESCAPE):
        if data.startswith('LOCATION'):
            location = data.split(" ") 
            INTERNET_GATEWAY_DEVICE_LOCATIONS[addr] = location[1]
            
def processIGDLocations():
    for addr in INTERNET_GATEWAY_DEVICE_LOCATIONS:
        location = INTERNET_GATEWAY_DEVICE_LOCATIONS[addr]
        payload = Http.send(location)
        root = ET.fromstring(payload)
        baseUrl = urlparse(location)
        baseUrl = baseUrl.scheme + '://' + baseUrl.netloc
        services = root.findall(".//*{urn:schemas-upnp-org:device-1-0}serviceList/")
        for service in services:
            serviceType = service.find('./{urn:schemas-upnp-org:device-1-0}serviceType').text
            if serviceType == 'urn:schemas-upnp-org:service:WANIPConnection:1':
                controlUrl = service.find('./{urn:schemas-upnp-org:device-1-0}controlURL').text
                INTERNET_GATEWAY_DEVICES.append(baseUrl + controlUrl)
    
def getExternalIPAddress():
    with open("recip/network/messages/upnp/GetExternalIPAddress.xml", "r") as upnp:
        payload = upnp.read()
        headers = {
            'SOAPAction': '"urn:schemas-upnp-org:service:WANIPConnection:1#GetExternalIPAddress"',
            'Content-Type': 'text/xml'
        }
        for igd in INTERNET_GATEWAY_DEVICES:
            xml = Http.send(igd, payload, False, headers)
            return xmlFindText(xml, 'NewExternalIPAddress')

def addPortMapping(port):
    with open("recip/network/messages/upnp/AddPortMapping.xml", "r") as upnp:
        payload = upnp.read()
        payload = payload % (port,
                             port,
                             Network.getIpAddress(False),
                             Config.getValue('NODE_VERSION'))
        headers = {
            'SOAPAction': '"urn:schemas-upnp-org:service:WANIPConnection:1#AddPortMapping"',
            'Content-Type': 'text/xml'
        }
        for igd in INTERNET_GATEWAY_DEVICES:
            xml = Http.send(igd, payload, False, headers)
            return xmlFindText(xml, 'AddPortMappingResponse')

def deletePortMapping(port):
    with open("recip/network/messages/upnp/DeletePortMapping.xml", "r") as upnp:
        payload = upnp.read()
        payload = payload % (port)
        headers = {
            'SOAPAction': '"urn:schemas-upnp-org:service:WANIPConnection:1#DeletePortMapping"',
            'Content-Type': 'text/xml'
        }
        for igd in INTERNET_GATEWAY_DEVICES:
            xml = Http.send(igd, payload, False, headers)
            return xmlFindText(xml, 'DeletePortMappingResponse')