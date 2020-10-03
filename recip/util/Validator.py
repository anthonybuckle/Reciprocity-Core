from recip.util import Config
from recip.util import Chain

def coinbaseMaturity(height):
    chainHeadIndexBlock = Chain.getChain().getChainHeadIndexBlock()
    if Config.getIntValue('COINBASE_MATURITY') > chainHeadIndexBlock.height - height:
        return False
    return True

def address(address):
    if address == None:
        return False
    if len(address) != Config.getIntValue('ADDRESS_LEN'):
        return False
    return True

def public(public):
    if public == None:
        return False
    if len(public) != Config.getIntValue('PUBLIC_LEN'):
        return False
    return True

def signature(signature):
    if signature == None:
        return False
    if len(signature) != Config.getIntValue('SIGNATURE_LEN'):
        return False
    return True

def private(private):
    if private == None:
        return False
    if len(private) != Config.getIntValue('PRIVATE_LEN'):
        return False
    return True

def hash(hash):
    if hash == None:
        return False
    if len(hash) != Config.getIntValue('HASH_LEN'):
        return False
    return True

def host(host):
    if host == None:
        return False
    if not len(host) > 0:
        return False
    return True

def value(value, zero=False):
    if value == None:
        return False
    if zero:
        if not value >= 0:
            return False
    else:
        if not value > 0:
            return False
    return True
    
def gasLimit(gasLimit):
    if gasLimit == None:
        return False
    if gasLimit < 0:
        return False
    return True

def gasPrice(gasPrice):
    if gasPrice == None:
        return False
    if gasPrice < 0:
        return False
    return True
