from recip.core.Input import Input
from recip.core.Output import Output
from recip.util.Serializable import Serializable
from recip.storage import Accounts
from recip.util import Config
from recip.util import Crypto
from recip.util import DataType
from recip.util import RLP
from recip.storage import UXTO

class Transaction(Serializable):
    def __init__(self, gasLimit = None, gasPrice = None):
        self.version = Config.getIntValue("TRANSACTION_VERSION")

        self.gasLimit = gasLimit
        self.gasPrice = gasPrice
        self.gasRemaining = None

        self.inputs = []
        self.outputs = []
        self.internalOutputs = []
            
    def hash(self):
        includeWitness = self.isCoinbase()
        return Crypto.generateHash(self.serialize(includeWitness))
    
    def hashTxWitness(self):
        return Crypto.generateHash(self.serialize())
    
    def isCoinbase(self):
        if len(self.inputs) != 1:
            return False
        return self.inputs[0].isCoinbase()

    def sign(self):
        signatures = {}
        
        for txIn in self.inputs:
            unspentTransactionCoin = UXTO.getUnspentTransactionCoin(txIn.outpoint)
            unspentTransactionOutput = unspentTransactionCoin.output
            
            outputHash = self.hashOutput(txIn, unspentTransactionOutput)
            
            account = None
            if unspentTransactionOutput.hasExtScript():
                account = Accounts.getAccountByAddress(txIn.witness[0])
            else:
                account = Accounts.getAccountByAddress(unspentTransactionOutput.address)
            if account.isMultiSig():
                _signatures = []
                for public in account.public:
                    _account = Accounts.getAccountByPublic(public)
                    signature = _account.sign(outputHash)
                    _signatures.append(signature)
                signatures[txIn.outpoint] = _signatures
            else:
                signature = account.sign(outputHash)
                signatures[txIn.outpoint] = signature
            
        for txIn in self.inputs:
            unspentTransactionCoin = UXTO.getUnspentTransactionCoin(txIn.outpoint)
            
            unspentTransactionOutput = unspentTransactionCoin.output
            
            account = None
            if unspentTransactionOutput.hasExtScript():
                account = Accounts.getAccountByAddress(txIn.witness[0])
            else:
                account = Accounts.getAccountByAddress(unspentTransactionOutput.address)
            if account.isMultiSig():
                signatures = signatures[txIn.outpoint]
                for signature, public in zip(signatures, account.public):
                    txIn.initWitness(signature, public)
            else:
                signature = signatures[txIn.outpoint]
                txIn.initWitness(signature, account.public)
            
    def hashOutput(self, txIn, txOut):
        witnesses = []
        for _txIn in self.inputs:
            witnesses.append(_txIn.witness)
            _txIn.witness = []
            
        txIn.witness = txOut.serialize()
            
        outputHash = self.hash()
            
        for idx in range(len(self.inputs)):
            self.inputs[idx].witness = witnesses[idx]
            
        return outputHash
             
    def addCoinbaseInput(self, coinbaseData):
        txIn = Input(Config.getBytesValue('COINBASE_TRANSACTION_ID', False), Config.getIntValue('COINBASE_OUTPUT_INDEX'))
        txIn.witness = coinbaseData
        self.inputs.append(txIn)
    
    def addInput(self, txId, outputIndex, witness = None):
        self.inputs.append(Input(txId, outputIndex, witness))

    def addOutput(self, address, script, value, extraData=None):
        self.outputs.append(Output(address, script, value, extraData))

    def addInternalOutput(self, address, script, value, extraData=None):
        self.internalOutputs.append(Output(address, script, value, extraData))

    def calculateTxFee(self):
        txInFee = 0
        for txIn in self.inputs:
            prevCoin = UXTO.getUnspentTransactionCoin(txIn.outpoint)
            if prevCoin != None:
                prevTxOut = prevCoin.output
                txInFee += prevTxOut.value
        txOutFee = 0
        for txOut in self.outputs:
            txOutFee += txOut.value
        txFee = txInFee - txOutFee
        if txFee < 0:
            return 0
        else:
            return txFee

    def calculateTxGasUsed(self):
        if self.gasRemaining == None:
            return 0
        return self.gasLimit - self.gasRemaining

    def serialize(self, includeWitness = True):
        witnesses = []
        if includeWitness:
            for txIn in self.inputs:
                witnesses.append(txIn.witness)
        item = [
            self.version,
            self.gasLimit,
            self.gasPrice,
            self.inputs,
            self.outputs,
            witnesses
        ]
        return RLP.encode(item)
    
    def deserialize(self, buffer):
        decodedBuffer = RLP.decode(buffer)
        self.version = DataType.deserialize(decodedBuffer[0], DataType.INT, 0)
        self.gasLimit = DataType.deserialize(decodedBuffer[2], DataType.INT, 0)
        self.gasPrice = DataType.deserialize(decodedBuffer[1], DataType.INT, 0)
        self.inputs = []
        for txInBuffer in decodedBuffer[3]:
            txIn = Input()
            txIn.deserialize(txInBuffer)
            self.inputs.append(txIn)
        self.outputs = []
        for txOutBuffer in decodedBuffer[4]:
            txOut = Output()
            txOut.deserialize(txOutBuffer)
            self.outputs.append(txOut)
        for txIn, witness in zip(self.inputs, decodedBuffer[5]):
            txIn.witness = witness
