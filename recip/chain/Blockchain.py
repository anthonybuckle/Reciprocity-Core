from recip.network.messages.core.types.Inv import InventoryType
from recip.mining.MiningWorker import MiningWorker
from recip.chain.MerkleTree import MerkleTree
from recip.storage.Storage import Storage
from recip.storage import OrphanManager
from recip.storage import MemoryPool
from threading import RLock
from recip.storage import UXTO
from recip.core.Block import Block
from recip.core.Coin import Coin
from recip.core.IndexBlock import IndexBlock
from recip.core.Transaction import Transaction
from recip.core.Outpoint import Outpoint
from recip.util import Address
from recip.util import Bits
from recip.util import Config
from recip.util import DataType
from recip.util import Sync
from recip.util import Units
from recip.vm import Script
from recip.validate import ValidatorFactory, ValidatorType
import math

class Blockchain(object):
    def __init__(self):
        self.db = Config.getFilePath("CHAIN_DIRECTORY", "BLOCKCHAIN_DB")
        self.subDb = Config.getValue("BLOCKS_SUB_DB")
        
        self.storage = Storage(self.db, self.subDb)
           
        self.indexDb = Config.getFilePath("CHAIN_DIRECTORY", "INDEX_DB")
        self.subIndexDb = Config.getValue("INDEX_SUB_DB")
        
        self.index = Storage(self.indexDb, self.subIndexDb)
        
        self.CHAIN_HEAD_INDEX = DataType.serialize("CHAIN_HEAD_INDEX")
        self.BLOCK_HEIGHT_KEY = "BLOCK_HEIGHT_KEY"
        
        self.blkValidator = ValidatorFactory.getInstance(ValidatorType.BLOCK)
        self.txValidator = ValidatorFactory.getInstance(ValidatorType.TX)
        
        self.blkLock = RLock()
        self.orphanLock = RLock()
        
        self.miningPool = {}
        
    def init(self):
        if self.getIndexBlockByHash(self.CHAIN_HEAD_INDEX) == None:
            genesisBlockGasLimit = Config.getIntValue("GENESIS_BLOCK_GAS_LIMIT")
            genesisBlockGasUsed = Config.getIntValue("GENESIS_BLOCK_GAS_USED")
            genesisBlockGasPrice = Config.getIntValue("GENESIS_BLOCK_GAS_PRICE")

            genesisBlock = Block()
            genesisBlock.previousHash = Config.getBytesValue("GENESIS_BLOCK_PREVIOUS_HASH", False)
            genesisBlock.gasLimit = genesisBlockGasLimit
            genesisBlock.gasUsed = genesisBlockGasUsed
            genesisBlock.nonce = Config.getIntValue("GENESIS_BLOCK_NONCE")
            genesisBlock.bits = Config.getIntValue("GENESIS_BLOCK_DIFFICULTY_BITS", 16)
            genesisBlock.timestamp = Config.getIntValue("GENESIS_BLOCK_TIMESTAMP")
            
            transaction = Transaction(genesisBlockGasLimit, genesisBlockGasPrice)
            coinbaseData = []
            coinbaseData.append(Config.getValue("GENESIS_BLOCK_COINBASE_DATA"))
            transaction.addCoinbaseInput(coinbaseData)
            genesisBlockRewards = Config.getDecimalValue("GENESIS_BLOCK_REWARDS")
            genesisBlockRewards = Units.toUnits(genesisBlockRewards)
            genesisBlockPublicAddress = Config.getValue("GENESIS_BLOCK_PUBLIC_ADDRESS")
            genesisBlockPublicAddress = Address.toAddressBytes(genesisBlockPublicAddress)
            genesisBlockScript = Script.verifySignature()
            transaction.addOutput(genesisBlockPublicAddress, genesisBlockScript, genesisBlockRewards)
            transaction.hash()
            
            genesisBlock.transactions.append(transaction) 
            genesisBlock.merkleRoot = MerkleTree.getMerkleRoot(genesisBlock.transactions, False)
            genesisBlock.witnessRoot = MerkleTree.getMerkleRoot(genesisBlock.transactions, True)
            
            self.addBlock(genesisBlock)
    
    def acquireBlockLock(self):
        self.blkLock.acquire()
        
    def releaseBlockLock(self):
        self.blkLock.release()

    def acquireOrphanLock(self, blocking=True):
        return self.orphanLock.acquire(blocking)
        
    def releaseOrphanLock(self):
        self.orphanLock.release()

    def getBlockHashByHeight(self, height):
        blockHeightKey = "{0}{1}{2}".format(self.BLOCK_HEIGHT_KEY, '_', height)
        blockHeightKey = DataType.serialize(blockHeightKey)
        return self.index.get(blockHeightKey)

    def getBlockByHash(self, blockHash):
        blockHashBytes = DataType.serialize(blockHash)
        blockBytes = self.storage.get(blockHashBytes)
        return self.getBlockFromBytes(blockBytes)
    
    def getChainHeadBlock(self):
        chainHeadIndexBlockBytes = self.index.get(self.CHAIN_HEAD_INDEX)
        chainHeadIndexBlock = self.getIndexBlockFromBytes(chainHeadIndexBlockBytes)
        if chainHeadIndexBlock != None:
            return self.getBlockByHash(chainHeadIndexBlock.previousHash)
        else:
            return None
        
    def getBlockFromBytes(self, blockBytes):
        if blockBytes != None:
            block = Block()
            block.deserialize(blockBytes)
            return block
        return None
    
    def getIndexBlockByHash(self, blockHash):
        blockHashBytes = DataType.serialize(blockHash)
        indexBlockBytes = self.index.get(blockHashBytes)
        return self.getIndexBlockFromBytes(indexBlockBytes)
    
    def getChainHeadIndexBlock(self):
        chainHeadIndexBlockBytes = self.index.get(self.CHAIN_HEAD_INDEX)
        return self.getIndexBlockFromBytes(chainHeadIndexBlockBytes)
    
    def getIndexBlockFromBytes(self, indexBlockBytes):
        if indexBlockBytes != None:
            indexBlock = IndexBlock()
            indexBlock.deserialize(indexBlockBytes)
            return indexBlock
        return None

    def getNewBlock(self, address, previousHash, bits, extraNonce):
        previousIndexBlock = self.getIndexBlockByHash(previousHash)
        block = Block()

        gasLimit = Config.getIntValue("BLOCK_REWARDS_GAS_LIMIT")
        gasPrice = Config.getIntValue("BLOCK_REWARDS_GAS_PRICE")
        transaction = Transaction(gasLimit, gasPrice)

        height = previousIndexBlock.height + 1
        coinbaseData = [
            DataType.asString(height), 
            DataType.asString(bits), 
            DataType.asString(extraNonce)
        ]
        transaction.addCoinbaseInput(coinbaseData)
        block.transactions.append(transaction) 
        txFees = 0
        totalTxGasUsed = 0
        unconfirmedTransactions = MemoryPool.getMemoryPool()
        for txId in unconfirmedTransactions:
            unconfirmedTransaction = unconfirmedTransactions[txId]
            block.transactions.append(unconfirmedTransaction)  
            txFees += unconfirmedTransaction.calculateTxFee()
            totalTxGasUsed += unconfirmedTransaction.calculateTxGasUsed()
        blockRewards = Config.getDecimalValue("BLOCK_REWARDS")
        blockRewards = Units.toUnits(blockRewards)
        coinbaseValue = blockRewards + txFees
        script = Script.verifySignature()

        transaction.addOutput(address, script, coinbaseValue)
        transaction.hash()

        #Include coinbase tx gas used
        totalTxGasUsed += transaction.calculateTxGasUsed()

        block.merkleRoot = MerkleTree.getMerkleRoot(block.transactions, False)
        block.witnessRoot = MerkleTree.getMerkleRoot(block.transactions, True)

        blockGasLimit = previousIndexBlock.gasLimit + (previousIndexBlock.gasLimit * (1 / 1024))
        blockGasLimit = math.ceil(blockGasLimit)

        block.gasLimit = blockGasLimit
        block.gasUsed = totalTxGasUsed
        block.nonce = 0
        block.bits = bits
        block.previousHash = previousHash
        return block

    '''
        Add block into the tree. There are three cases: 
            1. block further extends the main branch; 
            2. block extends a side branch but does not add enough difficulty to make it become the new main branch; 
            3. block extends a side branch and makes it the new main branch.
    '''   
    def addBlock(self, block):
        if self.blkValidator.validate(block):
            try:
                self.acquireBlockLock()
            
                blockHash = block.hash()
                blockHashBytes = DataType.serialize(blockHash)
                
                if self.index.get(blockHashBytes) == None:
                    if not OrphanManager.hasBlock(blockHash):
                        bits = block.bits
                        previousChainWork = None
                        previousHash = block.previousHash
                        blockGasLimit = block.gasLimit
                        blockHeight = 0
                        
                        chainHeadBlock = self.getChainHeadBlock()
                        chainHeadIndexBlock = self.getIndexBlockByHash(self.CHAIN_HEAD_INDEX)
                        previousIndexBlock = self.getIndexBlockByHash(previousHash)
                        
                        if chainHeadIndexBlock == None:
                            chainHeadIndexBlock = IndexBlock()
                        if previousIndexBlock != None:
                            blockHeight = previousIndexBlock.height + 1
                            previousChainWork = previousIndexBlock.chainWork
                            
                        if blockHash == Config.getBytesValue('GENESIS_BLOCK_HASH'):
                            previousChainWork = Config.getIntValue('GENESIS_BLOCK_CHAIN_WORK', 16)
                        
                        '''        
                            For case 1, adding to main branch:
                        '''
                        if previousHash == chainHeadIndexBlock.previousHash or blockHash == Config.getBytesValue('GENESIS_BLOCK_HASH'):                
                            '''
                                For all but the coinbase transaction, apply the following:
                            '''
                            if not self.blkValidator.verifyNonCoinbaseTransactions(block):
                                return False
                                 
                            '''
                                Reject if coinbase value > sum of block creation fee and transaction fees
                            '''   
                            if not self.blkValidator.verifyCoinbaseValue(block):
                                return False
                                    
                            for transaction in block.transactions:
                                for txIn in transaction.inputs:
                                    UXTO.removeUnspentTransactionCoin(txIn.outpoint)
                                uxtoOutputs = []
                                uxtoOutputs.extend(transaction.outputs)
                                uxtoOutputs.extend(transaction.internalOutputs)
                                txOutputSize = 0
                                for txOut in uxtoOutputs:
                                    if txOut.store:
                                        txOutputSize += 1
                                outputIndex = 0
                                for txOut in uxtoOutputs:
                                    UXTO.removeStaleUnspentTransactionScript(txOut)
                                    if txOut.store:
                                        coin = Coin()
                                        coin.output = txOut
                                        coin.txOutputSize = txOutputSize
                                        coin.height = blockHeight
                                        coin.coinbase = transaction.isCoinbase()
                                        UXTO.addUnspentTransactionCoin(Outpoint(transaction.hash(), outputIndex), coin)
                                        outputIndex += 1
                                        '''
                                            For each transaction, "Add to wallet if mine"
                                        '''

                                '''
                                    For each transaction in the block, delete any matching transaction from the transaction pool
                                '''
                                MemoryPool.removeTransaction(transaction)
                                
                            chainHeadIndexBlock.chainWork = Bits.getChainworkFromBits(previousChainWork, bits)
                            chainHeadIndexBlock.previousHash = blockHash
                            chainHeadIndexBlock.gasLimit = blockGasLimit
                            chainHeadIndexBlock.height = blockHeight
                            self.index.set(self.CHAIN_HEAD_INDEX, chainHeadIndexBlock.serialize())
                        else:
                            blockChainWork = Bits.getChainworkFromBits(previousChainWork, bits)
                            chainHeadWork = chainHeadIndexBlock.chainWork
                            
                            hasNewMainChain = blockChainWork > chainHeadWork
                            
                            if hasNewMainChain:
                                '''
                                    For case 3, a side branch becoming the main branch:
                                '''
                            else:
                                '''
                                    For case 2, adding to a side branch, we don't do anything.
                                '''
                
                            if hasNewMainChain:
                                '''
                                    Find the fork block on the main branch which this side branch forks off of
                                '''
                                forkBlockHash = self.searchForkBlockHash(previousIndexBlock, chainHeadIndexBlock)
                                
                                '''
                                    Redefine the main branch to only go up to this fork block
                                    
                                    We will set new main chain head below
                                '''
                                
                                isNewMainChainValid = True
                                
                                '''
                                    For each block on the side branch, from the child of the fork block to the leaf, add to the main branch:
                                '''
                                prevBlock = self.getBlockByHash(block.previousHash)
                                while prevBlock.hash() != forkBlockHash:
                                    '''
                                        Do "branch" checks 3-11
                                    '''
                                    '''
                                        3) Transaction list must be non-empty
                                    '''
                                    if not self.blkValidator.verifyTransactionsNonEmpty(prevBlock):
                                        isNewMainChainValid = False
                                    
                                    '''
                                        4) Block hash must satisfy claimed nBits proof of work
                                    '''
                                    if not self.blkValidator.validateBlockBits(prevBlock.serializeHeader(), prevBlock.bits):
                                        isNewMainChainValid = False
                                    
                                    '''
                                        5) Block timestamp must not be more than two hours in the future
                                    '''
                                    if not self.blkValidator.verifyFutureTimestamp(prevBlock):
                                        isNewMainChainValid = False
                                        
                                    '''
                                        6) First transaction must be coinbase (i.e. only 1 input, with hash=0, n=-1), the rest must not be
                                    '''
                                    if not self.blkValidator.verifyInitialCoinbaseTransaction(prevBlock):
                                        isNewMainChainValid = False
                                        
                                    '''
                                        7) For each transaction, apply "tx" checks 2-4
                                            2) Make sure neither in or out lists are empty
                                            3) Size in bytes <= TRANSACTION_SIZE_LIMIT
                                            4) Each output value, as well as the total, must be in legal money range
                                    '''
                                    for transaction in prevBlock.transactions:
                                        if not self.txValidator.verifyInputOutputNonEmpty(transaction):
                                            isNewMainChainValid = False
                                        if not self.txValidator.verifyTransactionSizeLimit(transaction):
                                            isNewMainChainValid = False
                                        if not self.txValidator.verifyAllowedOutputValueRange(transaction):
                                            isNewMainChainValid = False
                                        
                                        '''
                                            8) For the coinbase (first) transaction, scriptSig length must be 2-100
                                        '''
                                        if not self.blkValidator.verifyCoinbaseWitnessLength(transaction):
                                            isNewMainChainValid = False
                                        
                                        '''
                                            9) Reject if sum of transaction sig opcounts > MAX_BLOCK_SIGOPS
                                        '''
                                        if not self.blkValidator.verifyMaxBlockSigOps(transaction):
                                            isNewMainChainValid = False
                                        
                                    '''
                                        10) Verify Merkle hash
                                    '''
                                    if not self.blkValidator.verifyMerkleHash(prevBlock):
                                        isNewMainChainValid = False
                                        
                                    '''
                                        Verify Witness hash
                                    '''
                                    if not self.blkValidator.verifyWitnessHash(prevBlock):
                                        isNewMainChainValid = False
                                        
                                    '''
                                        11) Check if prev block (matching prev hash) is in main branch or side branches. If not, add this to orphan blocks, 
                                        then query peer we got this from for 1st missing orphan block in prev chain; done with block
                                    '''
                                    if blockHash != Config.getBytesValue('GENESIS_BLOCK_HASH') and self.getBlockByHash(prevBlock.previousHash) == None:
                                        OrphanManager.addBlock(prevBlock)
                                        isNewMainChainValid = False
                                
                                    '''
                                        For all but the coinbase transaction, apply the following:
                                    '''
                                    if not self.blkValidator.verifyNonCoinbaseTransactions(prevBlock):
                                        isNewMainChainValid = False
                                    
                                    '''
                                        Reject if coinbase value > sum of block creation fee and transaction fees
                                    '''   
                                    if not self.blkValidator.verifyCoinbaseValue(prevBlock):
                                        isNewMainChainValid = False
                                    
                                    '''
                                        (If we have not rejected):
                                    '''
                                    if not isNewMainChainValid:
                                        break
                                    
                                    '''         
                                        For each transaction, "Add to wallet if mine"
                                    '''
                                        
                                    prevBlock = self.getBlockByHash(prevBlock.previousHash)
                                
                                '''
                                    If we reject at any point, leave the main branch as what it was originally, done with block
                                '''
                                if isNewMainChainValid:
                                    chainHeadIndexBlock.chainWork = blockChainWork
                                    chainHeadIndexBlock.previousHash = blockHash 
                                    chainHeadIndexBlock.gasLimit = blockGasLimit
                                    chainHeadIndexBlock.height = blockHeight
                                    self.index.set(self.CHAIN_HEAD_INDEX, chainHeadIndexBlock.serialize())
                                    
                                    '''
                                        For each block in the old main branch, from the leaf down to the child of the fork block:
                                    '''
                                    oldBlock = chainHeadBlock
                                    while oldBlock.hash() != forkBlockHash:
                                        '''
                                            For each non-coinbase transaction in the block:
                                        '''
                                        for transaction in oldBlock.transactions:
                                            if not transaction.isCoinbase():
                                                '''
                                                    Apply "tx" checks 2-9
                                                '''
                                                isTxValid = True
                                                
                                                '''
                                                    2) Make sure neither in or out lists are empty
                                                '''
                                                if not self.txValidator.verifyInputOutputNonEmpty(transaction):
                                                    isTxValid = False
                                                
                                                '''
                                                    3) Size in bytes <= TRANSACTION_SIZE_LIMIT
                                                '''
                                                if not self.txValidator.verifyTransactionSizeLimit(transaction):
                                                    isTxValid = False
                                                
                                                '''
                                                    4) Each output value, as well as the total, must be in legal money range
                                                '''
                                                if not self.txValidator.verifyAllowedOutputValueRange(transaction):
                                                    isTxValid = False
                                                
                                                '''
                                                    5) Make sure none of the inputs have hash=0, n=-1 (coinbase transactions)
                                                '''
                                                if not self.txValidator.verifyInputsNonCoinbase(transaction):
                                                    isTxValid = False
                                                
                                                '''
                                                    6) size in bytes >= 100[2]
                                                '''
                                                if not self.txValidator.verifyTransactionRequiredSize(transaction):
                                                    isTxValid = False
                                                
                                                '''
                                                    sig opcount <= 2[3]
                                                    3) The number of signature operands in the signature (no, that is not redundant) for standard transactions will never exceed two
                                                    7) Reject "nonstandard" transactions: scriptSig doing anything other than pushing numbers on the stack, 
                                                    or script not matching the two usual forms[4]
                                                '''
                                                if not self.txValidator.verifyAddress(transaction):
                                                    isTxValid = False
                                                if not self.txValidator.verifyExtraData(transaction):
                                                    isTxValid = False
                                                if not self.txValidator.verifyScript(transaction):
                                                    isTxValid = False
                                                if not self.txValidator.verifyWitness(transaction):
                                                    isTxValid = False
                                                
                                                '''
                                                    8) Reject if we already have matching tx in the pool,
                                                    except in step 8, only look in the transaction pool for duplicates, not the main branch
                                                '''
                                                if not self.txValidator.verifyTransactionDuplicateInPool(transaction):
                                                    isTxValid = False
                                                
                                                '''
                                                    9) For each input, if the referenced output exists in any other tx in the pool, reject this transaction
                                                '''
                                                if not self.txValidator.verifyTxOutputDuplicateInPool(transaction):
                                                    isTxValid = False
                                                
                                                '''
                                                    Add to transaction pool if accepted, else go on to next transaction
                                                '''
                                                if isTxValid:
                                                    MemoryPool.addSignedTransaction(transaction)

                                            outputIndex = 0
                                            for txOut in transaction.outputs:
                                                UXTO.removeUnspentTransactionCoin(Outpoint(transaction.hash(), outputIndex))
                                                outputIndex += 1

                                        oldBlock = self.getBlockByHash(oldBlock.previousHash)
                                    
                                    '''
                                        For each block in the new main branch, from the child of the fork node to the leaf:
                                    '''
                                    newMainBranchBlocks = []
                                        
                                    prevBlock = block
                                    while prevBlock.hash() != forkBlockHash:
                                        newMainBranchBlocks.insert(0, prevBlock)
                                        prevBlock = self.getBlockByHash(prevBlock.previousHash)
                                        
                                    for newMainBranchBlock in newMainBranchBlocks:
                                        newMainBranchBlockHash = newMainBranchBlock.hash()
                                        newMainBranchIndexBlock = None
                                        if newMainBranchBlockHash == blockHash:
                                            newMainBranchIndexBlock = chainHeadIndexBlock
                                        else:
                                            newMainBranchIndexBlock = self.getIndexBlockByHash(newMainBranchBlockHash)
                                        for transaction in newMainBranchBlock.transactions:
                                            for txIn in transaction.inputs:
                                                UXTO.removeUnspentTransactionCoin(txIn.outpoint)
                                            uxtoOutputs = []
                                            uxtoOutputs.extend(transaction.outputs)
                                            uxtoOutputs.extend(transaction.internalOutputs)
                                            txOutputSize = 0
                                            for txOut in uxtoOutputs:
                                                if txOut.store:
                                                    txOutputSize += 1
                                            outputIndex = 0
                                            for txOut in uxtoOutputs:
                                                UXTO.removeStaleUnspentTransactionScript(txOut)
                                                if txOut.store:
                                                    coin = Coin()
                                                    coin.output = txOut
                                                    coin.txOutputSize = txOutputSize
                                                    coin.height = newMainBranchIndexBlock.height
                                                    coin.coinbase = transaction.isCoinbase()
                                                    UXTO.addUnspentTransactionCoin(Outpoint(transaction.hash(), outputIndex), coin)
                                                    outputIndex += 1
                                                    '''
                                                        For each transaction, "Add to wallet if mine"
                                                    '''

                                            '''
                                                For each transaction in the block, delete any matching transaction from the transaction pool
                                            '''
                                            MemoryPool.removeTransaction(transaction)
                        '''
                            (If we have not rejected):
                        '''
                        self.storage.set(blockHashBytes, block.serialize())

                        blockHeightKey = "{0}{1}{2}".format(self.BLOCK_HEIGHT_KEY, '_', blockHeight)
                        blockHeightKey = DataType.serialize(blockHeightKey)
                        self.index.set(blockHeightKey, blockHashBytes)
                        
                        indexBlock = IndexBlock()
                        indexBlock.chainWork = Bits.getChainworkFromBits(previousChainWork, bits)
                        indexBlock.previousHash = previousHash 
                        indexBlock.gasLimit = blockGasLimit
                        indexBlock.height = blockHeight
                        self.index.set(blockHashBytes, indexBlock.serialize())
        
                        '''
                            Relay block to our peers
                        '''
                        Sync.inv(InventoryType.BLOCK, blockHash)
                    
                    '''
                        For each orphan block for which this block is its prev, run all these steps (including this one) recursively on that orphan
                    '''
                    self.syncOrphanBlocks()
                    
                    return True
            finally:
                self.releaseBlockLock()
        '''
            For each orphan block for which this block is its prev, run all these steps (including this one) recursively on that orphan
        '''
        self.syncOrphanBlocks()
            
        '''     
            If we rejected, the block is not counted as part of the main branch
        '''
        return False
    
    '''
        For each orphan block for which this block is its prev, run all these steps (including this one) recursively on that orphan
    '''
    def syncOrphanBlocks(self):
        hasLock = False
        try:
            hasLock = self.acquireOrphanLock(False)
            if hasLock:
                orphanBlocks = []
                for orphanBlockHash in OrphanManager.getBlocks():
                    orphanBlock = OrphanManager.getBlock(orphanBlockHash)
                    previousHash = orphanBlock.previousHash
                    previousHashBytes = DataType.serialize(previousHash)
                    if self.index.get(previousHashBytes) != None:
                        orphanBlocks.append(orphanBlock)
                    elif not OrphanManager.hasBlock(previousHash):
                        Sync.getdata(InventoryType.BLOCK, previousHash)
                for orphanBlock in orphanBlocks:
                    OrphanManager.removeBlock(orphanBlock)
                for orphanBlock in orphanBlocks:
                    self.addBlock(orphanBlock)
        finally:
            if hasLock:
                self.releaseOrphanLock()
    
    def searchForkBlockHash(self, sideChainIndexBlock, chainHeadIndexBlock):
        sideChainBlock = sideChainIndexBlock
        chainHeadBlock = chainHeadIndexBlock
        while not chainHeadBlock.previousHash == sideChainBlock.previousHash:
            if chainHeadBlock.height > sideChainBlock.height:
                chainHeadBlock = self.getIndexBlockByHash(chainHeadBlock.previousHash)
            else:
                sideChainBlock = self.getIndexBlockByHash(sideChainBlock.previousHash)
        return chainHeadBlock.previousHash

    def addMiningWorker(self, account, enabled):
        miningWorker = MiningWorker(self, account, enabled)
        miningWorker.start()
        
        self.miningPool[account.address] = miningWorker
        
    def exitsMiningWorker(self, account):
        if account.address in self.miningPool:
            return True  
        else:
            return False

    def stopMiningWorker(self, account):
        miningWorker = self.miningPool[account.address]
        miningWorker.enabled = False
        self.miningPool.pop(account.address)
