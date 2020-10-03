from recip.storage import Accounts
from recip.storage import Contracts
from recip.storage.Storage import Storage
from recip.core.Contract import Contract
from recip.core.Coin import Coin
from recip.core.Outpoint import Outpoint
from recip.util import Address
from recip.util import DataType
from recip.util import Config
from recip.util import Log

class UXTO:
    db = Config.getFilePath("CHAIN_DIRECTORY", "STATE_DB")
    subDb = Config.getValue("UXTO_SUB_DB")
    uxto = Storage(db, subDb)
    
    indexDb = Config.getFilePath("CHAIN_DIRECTORY", "STATE_INDEX_DB")
    subIndexDb = Config.getValue("UXTO_INDEX_SUB_DB")
        
    index = Storage(indexDb, subIndexDb)

def getUnspentTransactionOutpointByAddress(address):
    outpointBytes = UXTO.index.get(address)
    if outpointBytes != None:
        outpoint = Outpoint()
        outpoint.deserialize(outpointBytes)
        return outpoint
    return None

def getUnspentTransactionScript(address):
    outpointScript = getUnspentTransactionOutpointByAddress(address)
    if outpointScript != None:
        unspentTransactionScript = getUnspentTransactionCoin(outpointScript)
        if unspentTransactionScript != None:
            txOut = unspentTransactionScript.output
            if txOut.hasExtScript():
                return unspentTransactionScript
    return None

def getUnspentTransactionCoin(outpoint):
    coinBytes = UXTO.uxto.get(outpoint.serialize())
    if coinBytes != None:
        coin = Coin()
        coin.deserialize(coinBytes)
        return coin
    return None

def hasUnspentTransactionCoin(outpoint):
    return not UXTO.uxto.get(outpoint.serialize()) == None

def addUnspentTransactionCoin(outpoint, coin):
    txOut = coin.output
    if txOut.hasExtScript():
        UXTO.index.set(txOut.address, outpoint.serialize())
        Contracts.addContract(Contract(txOut.address))
    elif Accounts.hasAddress(txOut.address):
        Accounts.addConfirmedBalanceByAddress(txOut.address, txOut.value)
        Accounts.addUnspentTransactionCoin(outpoint, coin)
    UXTO.uxto.set(outpoint.serialize(), coin.serialize())
    
def removeUnspentTransactionCoin(outpoint):
    coin = getUnspentTransactionCoin(outpoint)
    if coin != None:
        txOut = coin.output
        if txOut.hasExtScript():
            if outpoint.removal:
                UXTO.index.remove(txOut.address)
                Contracts.removeContract(txOut.address)
            else: 
                return
        elif Accounts.hasAddress(txOut.address):
            Accounts.subtractConfirmedBalanceByAddress(txOut.address, txOut.value)
            Accounts.removeUnspentTransactionCoin(outpoint)
    UXTO.uxto.remove(outpoint.serialize())

def removeStaleUnspentTransactionScript(output):
    if output.hasExtScript():
        unspentTransactionOutpoint = getUnspentTransactionOutpointByAddress(output.address)
        if unspentTransactionOutpoint != None:
            unspentTransactionOutpoint.removal = True
            removeUnspentTransactionCoin(unspentTransactionOutpoint)
