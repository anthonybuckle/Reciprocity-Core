from recip.chain.Blockchain import Blockchain

class Chain:
    blockchain = Blockchain()
    
def init():
    Chain.blockchain.init()
    
def getChain():
    return Chain.blockchain