from threading import RLock

class OrphanManager:
    transactions = {}
    blocks = {}
    
    txLock = RLock()
    blkLock = RLock()

def acquireTxLock():
    OrphanManager.txLock.acquire()
    
def releaseTxLock():
    OrphanManager.txLock.release()

def hasTransaction(txId):
    try:
        acquireTxLock()
        return txId in OrphanManager.transactions
    finally:
        releaseTxLock()

def getTransaction(txId):
    try:
        acquireTxLock()
        return OrphanManager.transactions[txId]
    finally:
        releaseTxLock()

def getTransactions():
    try:
        acquireTxLock()
        transactions = OrphanManager.transactions
        return transactions.copy()
    finally:
        releaseTxLock()
    
def removeTransaction(transaction):
    try:
        acquireTxLock()
        txHash = transaction.hash()
        if txHash in OrphanManager.transactions:
            OrphanManager.transactions.pop(txHash)
    finally:
        releaseTxLock()

def addTransaction(transaction):
    try:
        acquireTxLock()
        txId = transaction.hash()
        OrphanManager.transactions[txId] = transaction
    finally:
        releaseTxLock()
    
def acquireBlockLock():
    OrphanManager.blkLock.acquire()
    
def releaseBlockLock():
    OrphanManager.blkLock.release()
    
def hasBlock(blkHash):
    try:
        acquireBlockLock()
        return blkHash in OrphanManager.blocks
    finally:
        releaseBlockLock()

def getBlock(blkHash):
    try:
        acquireBlockLock()
        return OrphanManager.blocks[blkHash]
    finally:
        releaseBlockLock()

def getBlocks():
    try:
        acquireBlockLock()
        blocks = OrphanManager.blocks
        return blocks.copy()
    finally:
        releaseBlockLock()

def removeBlock(block):
    try:
        acquireBlockLock()
        blkHash = block.hash()
        if blkHash in OrphanManager.blocks:
            OrphanManager.blocks.pop(blkHash)
    finally:
        releaseBlockLock()
        
def addBlock(block):
    try:
        acquireBlockLock()
        blkHash = block.hash()
        OrphanManager.blocks[blkHash] = block
    finally:
        releaseBlockLock()