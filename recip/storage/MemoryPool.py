from recip.core.Contract import Contract
from recip.core.Transaction import Transaction
from recip.core.Coin import Coin
from recip.core.Outpoint import Outpoint
from recip.network.messages.core.types.Inv import InventoryType
from recip.storage.Accounts import Accounts
from recip.storage import UXTO
from recip.storage import OrphanManager
from recip.util import Config
from recip.util import Crypto
from recip.util import DataType
from recip.util import Sync
from recip.util import Validator
from recip.vm import Script
from recip.validate import ValidatorFactory, ValidatorType
from threading import RLock

class MemoryPool:
    memoryPool = {}
    txValidator = ValidatorFactory.getInstance(ValidatorType.TX)
    
    spentOutpoints = set() 
    
    txLock = RLock()

def getMemoryPool():
    return MemoryPool.memoryPool
    
def acquireTxLock():
    MemoryPool.txLock.acquire()
    
def releaseTxLock():
    MemoryPool.txLock.release()
    
def getTransactionById(txId):
    try:
        acquireTxLock()
        
        if txId in MemoryPool.memoryPool:
            return MemoryPool.memoryPool[txId]
        return None
    finally:
        releaseTxLock()
    
def removeTransaction(transaction):
    try:
        acquireTxLock()
        
        txHash = transaction.hash()
        if txHash in MemoryPool.memoryPool:
            MemoryPool.memoryPool.pop(txHash)
            
            for txIn in transaction.inputs:
                MemoryPool.spentOutpoints.remove(txIn.outpoint)
    finally:
        releaseTxLock()
    
def getUnconfirmedBalanceByAddress(address):
    try:
        acquireTxLock()
        
        unconfirmedBalance = 0
        for txHash in MemoryPool.memoryPool:
            transaction = MemoryPool.memoryPool[txHash]
            for output in transaction.outputs:
                if output.address == address:
                    unconfirmedBalance += output.value
        return unconfirmedBalance 
    finally:
        releaseTxLock()
    
def createUnconfirmedMultiSigTransaction(fromAccount, toAddress, value, gasLimit, gasPrice, threshold):
    transaction, outpoints = createNewUnconfirmedTransaction(fromAccount, value, gasLimit, gasPrice, Script.verifyMultiSignature())
    if transaction != None:
        #Multi signature value
        _script = Script.verifyMultiSignature()
        extraData = threshold
        transaction.addOutput(toAddress, script, value, extraData)
        transaction.sign()

    return transaction

def createUnconfirmedAtomicSwapTransaction(fromAccount, toAddress, value, gasLimit, gasPrice, script, extraData=None):
    transaction, outpoints = createNewUnconfirmedTransaction(fromAccount, value, gasLimit, gasPrice)    
    if transaction != None:
        #Atomic swap value
        transaction.addOutput(toAddress, script, value, extraData)
        transaction.sign()

    return transaction

def createUnconfirmedTransaction(fromAccount, toAddress, value, gasLimit, gasPrice, script=None, parameters=None):
    transaction, outpoints = createNewUnconfirmedTransaction(fromAccount, value, gasLimit, gasPrice)
    if transaction != None:
        if script != None or parameters != None:
            #smart contract
            if script == None:
                #call
                witness = []
                witness.append(fromAccount.address)
                witness.extend(parameters)

                unspentTransactionOutpoint = UXTO.getUnspentTransactionOutpointByAddress(toAddress)

                transaction.addInput(unspentTransactionOutpoint.txId, unspentTransactionOutpoint.outputIndex, witness)

                if value > 0:
                    #contract value transfer
                    _script = Script.merge()
                    transaction.addOutput(toAddress, _script, value)
            else:
                #deploy
                outpointBytes = bytearray()
                for outpoint in outpoints:
                    outpointBytes.extend(outpoint.serialize())
                extensionAddress = Crypto.generateAddress(outpointBytes)

                _script = bytearray()
                _script.append(Config.getIntValue("EXTENSION_SCRIPT_VERSION"))
                _script.extend(script)
                _script = DataType.serialize(_script)

                extraData = None
                if len(parameters) > 0:
                    extraData = parameters
                    extraData.append(fromAccount.address)
                    
                transaction.addOutput(extensionAddress, _script, value, extraData)
        else:
            _script = None
            unspentTransactionScript = UXTO.getUnspentTransactionScript(toAddress)
            if unspentTransactionScript != None:
                #contract value transfer
                _script = Script.merge()
            if _script == None:
                #value
                _script = Script.verifySignature()
            transaction.addOutput(toAddress, _script, value)
        
        transaction.sign()

    return transaction

def createNewUnconfirmedTransaction(fromAccount, value, gasLimit, gasPrice, script=Script.verifySignature(), extraData=None):
    spending = 0
    outpoints = set()
    fee = gasLimit * gasPrice
    try:
        Accounts.index.open(Accounts.localUxtoSubDb)
        with Accounts.index.db.begin() as local:
            for outpointBytes, coinBytes in local.cursor(db=Accounts.index.subDb):
                outpoint = Outpoint()
                coin = Coin()

                outpoint.deserialize(outpointBytes)
                coin.deserialize(coinBytes)

                txOut = coin.output

                if txOut.address != fromAccount.address:
                    continue
                if outpoint in MemoryPool.spentOutpoints:
                    continue
                if coin.isCoinbase():
                    if not Validator.coinbaseMaturity(coin.height):
                        continue
                outpoints.add(outpoint)
                spending += txOut.value
                if spending > value + fee: 
                    break
    except IOError:
        Log.error('Unable to open accounts local uxto database: %s' % Config.getValue("ACCOUNTS_INDEX_DB"))
    finally:
        Accounts.index.close()
    
    if spending < value + fee:
        return None, None

    transaction = Transaction(gasLimit, gasPrice)

    for outpoint in outpoints:
        transaction.addInput(outpoint.txId, outpoint.outputIndex)

    change = spending - value - fee
    if change > 0:
        transaction.addOutput(fromAccount.address, script, change, extraData)

    return transaction, outpoints

def addUnconfirmedMultiSigTransaction(fromAccount, publicKeys, signatures, toAddress, value, gasLimit, gasPrice, threshold=None):              
    try:
        acquireTxLock()
        transaction = createUnconfirmedMultiSigTransaction(fromAccount, toAddress, value, gasLimit, gasPrice, threshold)
        if transaction == None:
            return None
        for txIn in transaction.inputs:
            for publicKey, signature in zip(publicKeys, signatures):
                txIn.initWitness(signature, publicKey)
        if addSignedTransaction(transaction):
            return transaction.hash()
        else:
            return None
    finally:
        releaseTxLock()

def addUnconfirmedTransaction(fromAccount, toAddress, value, gasLimit, gasPrice, script=None, parameters=None):
    try:
        acquireTxLock()
        transaction = createUnconfirmedTransaction(fromAccount, toAddress, value, gasLimit, gasPrice, script, parameters)
        if transaction == None:
            return None
        if addSignedTransaction(transaction):
            return transaction.hash()
        else:
            return None
    finally:
        releaseTxLock()

def addSignedTransaction(transaction):
    if MemoryPool.txValidator.validate(transaction):
        try:
            acquireTxLock()
        
            txId = transaction.hash()
            '''
                Add to transaction pool[7]
            '''
            MemoryPool.memoryPool[txId] = transaction
            
            for txIn in transaction.inputs:
                MemoryPool.spentOutpoints.add(txIn.outpoint)
            
            '''
                Add to wallet if mine
            '''
        
            '''
                Relay transaction to peers
            '''
            Sync.inv(InventoryType.TRANSACTION, txId)
                
            '''
                For each orphan transaction that uses this one as one of its inputs, run all these steps (including this one) recursively on that orphan
            '''
            txOutputLen = len(transaction.outputs)
            orphanTransactions = []
            for txOrphan in OrphanManager.getTransactions():
                for txOrphanIn in txOrphan.inputs:
                    orphanOutPoint = txOrphanIn.outpoint
                    if orphanOutPoint.txId == txId and txOutputLen > orphanOutPoint.outputIndex:
                        orphanTransactions.append(txOrphan)
                        break
            for orphanTransaction in orphanTransactions:
                OrphanManager.removeTransaction(orphanTransaction)
            for orphanTransaction in orphanTransactions:
                addSignedTransaction(orphanTransaction)
                    
            return True

        finally:
            releaseTxLock()
            
    return False
