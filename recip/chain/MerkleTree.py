from recip.util import Crypto

class MerkleTree:
    def __init__(self, transactions, includeWitness):
        self.transactions = transactions
        self.includeWitness = includeWitness
        self.merkleNodes = []
        self.init()
        
    def init(self):
        merkleNodes = []
        for transaction in self.transactions:
            merkleNode = MerkleNode()
            txHash = transaction.hashTxWitness() if self.includeWitness else transaction.hash()
            merkleNode.hash = Crypto.generateHash(txHash)
            merkleNodes.append(merkleNode)           
        self.generateMerkleTree(merkleNodes)
        self.merkleNodes.extend(merkleNodes) 
        
    def generateMerkleTree(self, prevMerkleNodes):
        if len(prevMerkleNodes) > 1:
            merkleNodes = []
            merkleNode = None
            for prevMerkleNode in prevMerkleNodes:
                if merkleNode == None:
                    merkleNode = MerkleNode()
                if merkleNode.left == None:
                    merkleNode.left = prevMerkleNode
                elif merkleNode.right == None:
                    merkleNode.right = prevMerkleNode
                if merkleNode.left != None and merkleNode.right != None:
                    data = merkleNode.left.hash + merkleNode.right.hash
                    merkleNode.hash = Crypto.generateHash(data)
                    merkleNodes.append(merkleNode)   
                    merkleNode = None
            if merkleNode != None:         
                merkleNode.hash = Crypto.generateHash(merkleNode.left.hash)
                merkleNodes.append(merkleNode)   
            self.generateMerkleTree(merkleNodes)
            self.merkleNodes.extend(merkleNodes) 
            
    def getRootNode(self):
        return None if len(self.merkleNodes) == 0 else self.merkleNodes[0]

    @staticmethod
    def getMerkleRoot(transactions, includeWitness):
        merkleTree = MerkleTree(transactions, includeWitness)
        merkleNode = merkleTree.getRootNode()
        return None if merkleNode == None else merkleNode.hash
    
class MerkleNode:
    def __init__(self):
        self.left = None
        self.right = None
        self.hash = None
