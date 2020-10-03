from threading import Thread
from recip.validate import ValidatorFactory, ValidatorType
from recip.util import Address
from recip.util import Bits
from recip.util import TimeIt

class MiningWorker(Thread):
    def __init__(self, blockchain, account, enabled):
        Thread.__init__(self, name=Address.to0xAddress(account.address), daemon=True)
        self.blockchain = blockchain
        self.account = account
        self.enabled = enabled
        
        self.blkValidator = ValidatorFactory.getInstance(ValidatorType.BLOCK)
        self.MINING_KEY = 'MINING'
    
    def run(self):
        while self.enabled:
            TimeIt.start(self.MINING_KEY)
            
            chainHeadBlock = self.blockchain.getChainHeadBlock()
            chainHeadIndexBlock = self.blockchain.getChainHeadIndexBlock()

            previousHash = chainHeadBlock.hash()
            newBlockBits = Bits.getNewBlockBits(chainHeadBlock, chainHeadIndexBlock.height)
            extraNonce = 0
            
            block = self.blockchain.getNewBlock(self.account.address, previousHash, newBlockBits, extraNonce)

            validNonce = False
            while not validNonce:
                if not self.enabled:
                    return
                if self.blkValidator.validateBlockBits(block.serializeHeader(), newBlockBits):
                    validNonce = True 
                else:
                    block.nonce += 1
            
            self.blockchain.addBlock(block)
            
            TimeIt.stop(self.MINING_KEY)
            TimeIt.view(self.MINING_KEY)
