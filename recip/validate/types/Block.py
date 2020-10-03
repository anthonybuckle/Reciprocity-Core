from recip.validate import ValidatorFactory, ValidatorType
from recip.validate.Validator import Validator
from recip.chain.MerkleTree import MerkleTree
from recip.storage import OrphanManager
from recip.storage import UXTO
from recip.util import Bits
from recip.util import Config
from recip.util import Chain
from recip.util import Crypto
from recip.util import DataType
from recip.util import RLP
from recip.util import Units
import math

class Block(Validator):
    def __init__(self): 
        self.txValidator = ValidatorFactory.getInstance(ValidatorType.TX)
        
    def validate(self, block):
        '''
            Check syntactic correctness
        '''
        if block.version == None or block.version != Config.getIntValue("BLOCK_VERSION"):
            return False
        if block.previousHash == None or len(block.previousHash) != Config.getIntValue('HASH_LEN'):
            return False
        if block.merkleRoot == None or len(block.merkleRoot) != Config.getIntValue('HASH_LEN'):
            return False
        if block.witnessRoot == None or len(block.witnessRoot) != Config.getIntValue('HASH_LEN'):
            return False
        if block.gasLimit == None or block.gasLimit < 0:
            return False
        if block.gasUsed == None or block.gasUsed < 0:
            return False
        if block.nonce == None or block.nonce < 0:
            return False
        if block.bits == None or block.bits < 0:
            return False
        if block.timestamp == None or block.timestamp < 0:
            return False
        
        blkHash = block.hash()

        if block.previousHash == Config.getBytesValue('GENESIS_BLOCK_PREVIOUS_HASH', False):
            if blkHash != Config.getBytesValue('GENESIS_BLOCK_HASH'):
                print('Check Genesis Block Hash:', blkHash.hex())
                return False
        
        '''
            Reject if duplicate of block we have in any of the three categories
        '''
        
        '''
            1) blocks in the main branch
            the transactions in these blocks are considered at least tentatively confirmed
            
            2) blocks on side branches off the main branch
            these blocks have at least tentatively lost the race to be in the main branch
        '''
        if Chain.getChain().getBlockByHash(blkHash) != None:
            return False
        
        '''
            3) orphan blocks
            these are blocks which don't link into the main branch, normally because of a missing predecessor or nth-level predecessor
        '''
        if OrphanManager.hasBlock(blkHash):
            return False

        if not self.verifyTransactionsNonEmpty(block):
            return False
        
        '''
            Block hash must satisfy claimed nBits proof of work
        '''
        if not self.validateBlockBits(block.serializeHeader(), block.bits):
            return False
        
        if not self.verifyFutureTimestamp(block):
            return False
        
        if not self.verifyInitialCoinbaseTransaction(block):
            return False
        
        '''
            Check block gas limit
        '''
        totalTxGasLimit = 0
        for transaction in block.transactions:
            totalTxGasLimit += transaction.gasLimit

        if totalTxGasLimit > block.gasLimit:
            return False

        if block.gasUsed > block.gasLimit:
            return False

        previousBlockGasLimit = None
        if blkHash == Config.getBytesValue('GENESIS_BLOCK_HASH'):
            previousBlockGasLimit = Config.getIntValue('GENESIS_BLOCK_GAS_LIMIT')
        else:
            previousIndexBlock = Chain.getChain().getIndexBlockByHash(block.previousHash)
            if previousIndexBlock != None:
                previousBlockGasLimit = previousIndexBlock.gasLimit

        '''
            If previousBlockGasLimit is none, block is probably an orphan.
        '''
        if previousBlockGasLimit != None:
            maxBlockGasLimit = previousBlockGasLimit + (previousBlockGasLimit * (1 / 1024))
            maxBlockGasLimit = math.ceil(maxBlockGasLimit)

            # Check block gas limit increase a max of 1 / 1024
            if block.gasLimit > maxBlockGasLimit:
                return False
                
        '''
            Check block size in bytes
        '''
        if not self.verifyBlockSizeLimit(block):
            return False

        '''
            For each transaction, apply "tx" checks 2-4
                2) Make sure neither in or out lists are empty
                3) Size in bytes <= TRANSACTION_SIZE_LIMIT
                4) Each output value, as well as the total, must be in legal money range
        '''
        for transaction in block.transactions:
            if not self.txValidator.verifyInputOutputNonEmpty(transaction):
                return False
            if not self.txValidator.verifyTransactionSizeLimit(transaction):
                return False
            if not self.txValidator.verifyAllowedOutputValueRange(transaction):
                return False
        
            if not self.verifyCoinbaseWitnessLength(transaction):
                return False
            if not self.verifyMaxBlockSigOps(transaction):
                return False
        
        if not self.verifyMerkleHash(block):
            return False
            
        if not self.verifyWitnessHash(block):
            return False
            
        '''
            Check if prev block (matching prev hash) is in main branch or side branches. If not, add this to orphan blocks, then query peer we got this 
            from for 1st missing orphan block in prev chain; done with block
        '''
        if blkHash != Config.getBytesValue('GENESIS_BLOCK_HASH') and Chain.getChain().getBlockByHash(block.previousHash) == None:
            OrphanManager.addBlock(block)
           
        ''' 
            Check that nBits value matches the difficulty rules
        '''
        chainHeadBlock = None
        chainHeadBlockHeight = None

        if blkHash == Config.getBytesValue('GENESIS_BLOCK_HASH'):
            chainHeadBlock = block
            chainHeadBlockHeight = 0
        else:
            chainHeadBlock = Chain.getChain().getChainHeadBlock()
            chainHeadIndexBlock = Chain.getChain().getChainHeadIndexBlock()
            chainHeadBlockHeight = chainHeadIndexBlock.height
            
        newBlockBits = Bits.getNewBlockBits(chainHeadBlock, chainHeadBlockHeight)
        if block.bits != newBlockBits:
            return False
        
        '''
            Reject if timestamp is the median time of the last 11 blocks or before
        '''
        timestamps = []
        prevBlock = Chain.getChain().getBlockByHash(block.previousHash)
        while prevBlock != None and len(timestamps) <= 11:
            timestamps.append(prevBlock.timestamp)
            prevBlock = Chain.getChain().getBlockByHash(prevBlock.previousHash)
            
        if len(timestamps) == 11:
            timestamps.sort()
            if block.timestamp <= timestamps[5]:
                return False
        
        '''
            For certain old blocks (i.e. on initial block download) check that hash matches known values
        '''
            
        return True
    
    '''
        Transaction list must be non-empty
    '''
    def verifyTransactionsNonEmpty(self, block):
        if block.transactions == None or len(block.transactions) == 0:
            return False
        return True
    
    
    '''
        4) Block hash must satisfy claimed nBits proof of work
    '''
    def validateBlockBits(self, blockHeader, bits):
        currTarget = Bits.getTargetFromBits(bits)
        blockHeaderHash = Crypto.proofOfWorkHash(blockHeader)
        blockHeaderHashLong = DataType.bytesToInt(blockHeaderHash)
        if blockHeaderHashLong < currTarget:
            return True
        else:
            return False
    
    '''
        Block timestamp must not be more than two hours in the future
    '''
    def verifyFutureTimestamp(self, block):
        if block.timestamp - DataType.asTime() > 7200:
            return False
        return True
    
    ''' 
        First transaction must be coinbase (i.e. only 1 input, with hash=0, n=-1), the rest must not be
    '''
    def verifyInitialCoinbaseTransaction(self, block):
        checkCoinbase = True
        for transaction in block.transactions:
            if checkCoinbase:
                checkCoinbase = False
                if not transaction.isCoinbase():
                    return False
            else:
                if transaction.isCoinbase():
                    return False
        return True
    
    '''
        For the coinbase (first) transaction, witness length must be 2-100
    '''
    def verifyCoinbaseWitnessLength(self, transaction):
        if transaction.isCoinbase():
            txIn = transaction.inputs[0]
            witness = txIn.witness
            witnessEncoded = RLP.encode(witness)
            if len(witnessEncoded) < 2 or len(witnessEncoded) > 100:
                return False
        return True
    
    '''
        Reject if sum of transaction sig opcounts > MAX_BLOCK_SIGOPS
    '''
    def verifyMaxBlockSigOps(self, transaction):
        return True

    '''
        Check block size in bytes
    '''
    def verifyBlockSizeLimit(self, block):
        return True
    
    '''
        Verify Merkle hash
    '''
    def verifyMerkleHash(self, block):
        if block.merkleRoot != MerkleTree.getMerkleRoot(block.transactions, False):
            return False
        return True
    
    '''
        Verify Witness hash
    '''
    def verifyWitnessHash(self, block):
        if block.witnessRoot != MerkleTree.getMerkleRoot(block.transactions, True):
            return False
        return True
    
    def verifyNonCoinbaseTransactions(self, block):
        for transaction in block.transactions:
            if not transaction.isCoinbase():
                '''     
                    For each input, look in the main branch to find the referenced output transaction. Reject if the output transaction is missing for any input.
                    For each input, if the referenced output has already been spent by a transaction in the main branch, reject
                '''
                if not self.txValidator.verifyUxtoReferencedOutput(transaction):
                    return False
                
                '''
                    For each input, if we are using the nth output of the earlier transaction, but it has fewer than n+1 outputs, reject.
                '''
                for txIn in transaction.inputs:
                    outpoint = txIn.outpoint
                    unspentTransactionCoin = UXTO.getUnspentTransactionCoin(outpoint)
                    if unspentTransactionCoin.txOutputSize <= outpoint.outputIndex:
                        return False
                
                '''
                    For each input, if the referenced output transaction is coinbase (i.e. only 1 input, with hash=0, n=-1), 
                    it must have at least COINBASE_MATURITY (100) confirmations; else reject.
                '''
                if not self.txValidator.verifyCoinbaseMaturity(transaction):
                    return False
                                     
                '''
                    Verify crypto signatures for each input; reject if any are bad
                '''
                if not self.txValidator.verifyUnlockingScripts(transaction):
                    return False
                
                '''
                    Using the referenced output transactions to get input values, check that each input value, as well as the sum, are in legal money range
                '''
                if not self.txValidator.verifyAllowedInputValueRange(transaction):
                    return False
                   
                '''         
                    Reject if the sum of input values < sum of output values
                '''
                if not self.txValidator.verifySumInputOutputValues(transaction):
                    return False
        return True
    
    '''
        Reject if coinbase value > sum of block creation fee and transaction fees
    '''
    def verifyCoinbaseValue(self, block):
        coinbaseValue = 0.0
        blkCreationTxFees = Config.getDecimalValue("BLOCK_REWARDS")
        blkCreationTxFees = Units.toUnits(blkCreationTxFees)
        for transaction in block.transactions:
            if transaction.isCoinbase():
                output = transaction.outputs[0]
                coinbaseValue = output.value
            else:
                blkCreationTxFees += transaction.calculateTxFee()
        if coinbaseValue > blkCreationTxFees:
            return False
        return True
