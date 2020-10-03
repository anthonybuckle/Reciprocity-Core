from recip.core.Sidechain import Sidechain
from recip.util import Config
import json

class Sidechains:
    sidechains = []
    with open(Config.getValue('SIDECHAINS_DIR')) as _sidechains:  
        sidechainsJson = json.load(_sidechains)
        for sidechainJson in sidechainsJson:
            _sidechain = Sidechain()
            _sidechain.deserialize(sidechainJson)
            sidechains.append(_sidechain)
        
def getSidechains():
    return Sidechains.sidechains
    
def getSidechainByAddress(address):
    for sidechain in Sidechains.sidechains:
        if address == sidechain.address:
            return sidechain
    return None
    
def addSidechain(sidechain, save=True):
    if not sidechain in Sidechains.sidechains:
        Sidechains.sidechains.append(sidechain)
        if save:
            writeSidechains()
        return True
    else:
        return False
    
def removeSidechain(address, save=True):
    sidechain = getSidechainByAddress(address)
    if sidechain != None:
        Sidechains.sidechains.remove(sidechain)
        if save:
            writeSidechains()
        return True
    else:
        return False
        
def writeSidechains():
    sidechains = []
    for sidechain in Sidechains.sidechains:
        sidechains.append(sidechain.serialize())
    with open(Config.getValue('SIDECHAINS_DIR'), 'w') as sidechain:  
        json.dump(sidechains, sidechain, indent=2, sort_keys=False)