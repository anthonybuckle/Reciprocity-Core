from recip.storage.Storage import Storage
from recip.core.Peer import Peer
from recip.util import Config
from recip.util import Network
from recip.util import DataType
from recip.util import Sync
from recip.util import Log
from recip.util import Config
import json

class Peers:
    db = Config.getValue("PEERS_DB")
    subDb = Config.getValue("PEERS_SUB_DB")
    peers = Storage(db, subDb)
    
    hostname = Network.getHostname()
    ipAddress = Network.getIpAddress()

    if Config.getBoolValue('PEERS_ENABLE_SEEDS'):
        with open(Config.getValue('SEEDS_DIR')) as seeds:
            hosts = json.load(seeds)
            for host in hosts:
                if host != hostname and host != ipAddress:
                    hostBytes = DataType.serialize(host)
                    if peers.get(hostBytes) == None:
                        peer = Peer()
                        peer.host = host
                        peer.lastUpdate = DataType.asTime()
                        peers.set(hostBytes, peer.serialize())
        
def getPeers():
    peers = []
    try:
        Peers.peers.open()
        with Peers.peers.db.begin() as tx:
            cursor = tx.cursor(db=Peers.peers.subDb)
            while cursor.next():
                peerBytes = cursor.value()
                peer = getPeerFromBytes(peerBytes)
                if peer != None:
                    peers.append(peer)
    except IOError:
        Log.error('Unable to open peers database: %s' % Config.getValue("PEERS_DB"))
    finally:
        Peers.peers.close()
    return peers

def getPeerByHost(host):
    hostBytes = DataType.serialize(host)
    peerBytes = Peers.peers.get(hostBytes)
    return getPeerFromBytes(peerBytes)

def getPeerFromBytes(peerBytes):
    if peerBytes != None:
        peer = Peer()
        peer.deserialize(peerBytes)
        return peer
    return None

def addPeer(peer):
    peers = []
    peers.append(peer)
    addPeers(peers)
    
def addPeers(peers):
    for peer in peers: 
        if peer.host != Peers.hostname and peer.host != Peers.ipAddress:
            currPeer = getPeerByHost(peer.host)
            synchronized = False
            if currPeer == None:
                currPeer = peer
            else:
                currPeer.merge(peer)
                synchronized = True
            currPeer.lastUpdate = DataType.asTime()
            hostBytes = DataType.serialize(currPeer.host)
            Peers.peers.set(hostBytes, currPeer.serialize())
            if not synchronized:
                Sync.synchronize(currPeer.host)
                Sync.addr(currPeer.host)
    
def removePeer(peer):
    peers = []
    peers.append(peer)
    removePeers(peers)
    
def removePeers(peers):
    for peer in peers:
        hostBytes = DataType.serialize(peer.host)
        Peers.peers.remove(hostBytes)
    return True
