from recip.network.messages.core import MessageType, MessageFactory
from recip.network.messages.core.types.Inv import Inventory
from recip.util import Config
from recip.storage import Peers
import time

def synchronize(host):
    messageTypes = [
        MessageType.VERSION,
        MessageType.GETADDR,
        MessageType.GETBLOCKS,
        MessageType.MEMPOOL
    ]
    for messageType in messageTypes:
        synchronizeMessage(messageType, host)
        
def synchronizeMessage(messageType, host):
    message = MessageFactory.getInstance(messageType)
    processMessage(message, host)

def version():
    message = MessageFactory.getInstance(MessageType.VERSION)
    broadcastMessage(message)

def getaddr():
    message = MessageFactory.getInstance(MessageType.GETADDR)
    broadcastMessage(message)
       
def getdata(inventoryType, inventoryHash):
    message = MessageFactory.getInstance(MessageType.GETDATA)
    message.inventory.append(Inventory(inventoryType, inventoryHash))
    broadcastMessage(message)
          
def getblocks():
    message = MessageFactory.getInstance(MessageType.GETBLOCKS)
    broadcastMessage(message)
     
def mempool():
    message = MessageFactory.getInstance(MessageType.MEMPOOL)
    broadcastMessage(message)

def ping():
    message = MessageFactory.getInstance(MessageType.PING)
    while True:
        broadcastMessage(message)
        time.sleep(Config.getIntValue("PING_BROADCAST_SECONDS"))
     
def addr(host):
    message = MessageFactory.getInstance(MessageType.ADDR)
    message.addrList.append(host)
    broadcastMessage(message)
  
def inv(invType, invHash):
    message = MessageFactory.getInstance(MessageType.INV)
    inventory = []
    inventory.append(Inventory(invType, invHash))
    message.inventory.extend(inventory)
    message.count = len(inventory)
    broadcastMessage(message)

def broadcastMessage(message):
    peers = Peers.getPeers()
    if len(peers) > 0:
        for peer in peers.copy():
            processMessage(message, peer.host)
            
def processMessage(message, host):
    message.addrRecv = host
    message.send()