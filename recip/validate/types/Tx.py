from recip.core.Outpoint import Outpoint
from recip.validate.Validator import Validator
from recip.storage import OrphanManager
from recip.storage.UXTO import UXTO as UXTOStorage
from recip.storage import MemoryPool, UXTO
from recip.util import Chain
from recip.util import Config
from recip.util import Crypto
from recip.util import Units
from recip.vm.RVM import RVM
from recip.vm import Opcodes

class Tx(Validator):
        
    def validate(self, transaction):
        if transaction == None:
            return False
        
        '''
            The transaction’s syntax and data structure must be correct
        '''
        if transaction.version == None or transaction.version != Config.getIntValue('TRANSACTION_VERSION'):
            return False

        if not self.verifyInputOutputNonEmpty(transaction):
            return False
        
        for txIn in transaction.inputs:
            '''
                Check outpoint
            '''
            if txIn.outpoint == None:
                return False
            outpoint = txIn.outpoint
            if outpoint.txId == None or len(outpoint.txId) != Config.getIntValue('HASH_LEN'):
                return False
            if outpoint.outputIndex == None or outpoint.outputIndex < 0:
                return False
        
        '''
            Check Output Value
        '''
        for txOut in transaction.outputs:
            if txOut.value == None:
                return False
            if txOut.hasExtScript():
                if not txOut.value >= 0:
                    return False
            elif not txOut.value > 0:
                return False
        
        '''
            Check tx gas price and gas limit
        '''
        if transaction.gasPrice == None or transaction.gasPrice < 0:
            return False
        if transaction.gasLimit == None or transaction.gasLimit < 0:
            return False

        '''
            Internal Outputs are created from the result of a smart contract.
            Only the RVM should create them.
        '''
        if len(transaction.internalOutputs) > 0:
            return False

        if not self.verifyAddress(transaction):
            return False

        if not self.verifyExtraData(transaction):
            return False

        if not self.verifyScript(transaction):
            return False
        
        if not self.verifyWitness(transaction):
            return False
        
        if not self.verifyTransactionSizeLimit(transaction):
            return False
        
        '''
           Check for duplicate outpoints. 
        '''
        outpoints = set()
        for txIn in transaction.inputs:
            if txIn.outpoint in outpoints:
                return False
            outpoints.add(txIn.outpoint)
        
        if not self.verifyAllowedOutputValueRange(transaction):
            return False
        
        if not self.verifyInputsNonCoinbase(transaction):
            return False
        
        if not self.verifyTransactionRequiredSize(transaction):
            return False
        
        if not self.verifyTransactionDuplicateInPool(transaction):
            return False
        
        '''
            or txId in a block in the main branch
        '''
        txId = transaction.hash()
        try:               
            UXTOStorage.uxto.open()
            with UXTOStorage.uxto.db.begin() as uxto:
                cursor = uxto.cursor(db=UXTOStorage.uxto.subDb)
                while cursor.next():
                    outpointBytes = cursor.key()
                    outpoint = Outpoint()
                    outpoint.deserialize(outpointBytes)
                    if txId == outpoint.txId:
                        return False
        except IOError:
            Log.error('Unable to determine if txId is in a block in the main branch.')
        finally:
            UXTOStorage.uxto.close()

        if not self.verifyTxOutputDuplicateInPool(transaction):
            return False
        
        '''
            For each input, look in the main branch and the transaction pool to find the referenced output transaction. 
            If the output transaction is missing for any input, this will be an orphan transaction. Add to the orphan transactions, 
            if a matching transaction is not in there already.
        '''
        for txIn in transaction.inputs:
            outpoint = txIn.outpoint
            if not UXTO.hasUnspentTransactionCoin(outpoint):
                tx = MemoryPool.getTransactionById(outpoint.txId)
                if tx == None or len(tx.outputs) - 1 < outpoint.outputIndex:
                    OrphanManager.addTransaction(transaction)
                    return False
                
        if not self.verifyCoinbaseMaturity(transaction):
            return False
        
        if not self.verifyUxtoReferencedOutput(transaction):
            return False
        
        if not self.verifyAllowedInputValueRange(transaction):
            return False  
            
        if not self.verifySumInputOutputValues(transaction):
            return False  
            
        if not self.verifyUnlockingScripts(transaction):
            return False
            
        '''
            7) Note that when the transaction is accepted into the memory pool, an additional check is made to ensure that the coinbase value does not exceed 
            the transaction fees plus the expected BTC value (25BTC as of this writing).
        '''
        if transaction.isCoinbase():
            txOut = transaction.outputs
            blockRewards = Config.getDecimalValue("BLOCK_REWARDS")
            blockRewards = Units.toUnits(blockRewards)
            if txOut.value > blockRewards:
                return False
         
        return True
    
    '''
        Neither lists of inputs or outputs are empty
    '''
    def verifyInputOutputNonEmpty(self, transaction):
        if transaction.inputs == None or len(transaction.inputs) == 0:
            return False
        if transaction.outputs == None or len(transaction.outputs) == 0:
            return False
        return True
    
    '''
        Check Signature Script
        The number of signature operands in the signature (no, that is not redundant) for standard transactions will never exceed two
    '''
    def verifyWitness(self, transaction):
        for txIn in transaction.inputs:
            witness = txIn.witness
            if witness == None or len(witness) == 0:
                return False
            unspentTransactionCoin = UXTO.getUnspentTransactionCoin(txIn.outpoint);
            txOut = unspentTransactionCoin.output
            if txOut.hasExtScript():
                if len(witness) < Config.getIntValue('EXTENSION_INPUT_WITNESS_LEN'):
                    return False
            if txOut.isMultiSig() or txOut.isAtomicSwap() or txOut.isAtomicLock():
                if len(witness) % 2 == 0:
                    publicKeys = witness[::2]
                    signatures = witness[1::2]
                    for publicKey, signature in zip(publicKeys, signatures):
                        '''
                            The unlocking script (witness) can only push numbers on the stack
                        '''
                        if signature == None or len(signature) != Config.getIntValue('SIGNATURE_LEN'):
                            return False
                        if publicKey == None or len(publicKey) != Config.getIntValue('PUBLIC_LEN'):
                            return False
                else:
                    return False
            else:
                if len(witness) != Config.getIntValue('INPUT_WITNESS_LEN'):
                    return False
                '''
                    The unlocking script (witness) can only push numbers on the stack
                '''
                if witness[0] == None or len(witness[0]) != Config.getIntValue('SIGNATURE_LEN'):
                    return False
                if witness[1] == None or len(witness[1]) != Config.getIntValue('PUBLIC_LEN'):
                    return False

            if txOut.hasExtScript():
                address = txOut.address
                if address == None or len(address) != Config.getIntValue('ADDRESS_LEN'):
                    return False
        return True
    
    '''
        Check Public Key Script
        the locking script (script) must match Standard forms (this rejects “nonstandard” transactions)
    '''
    def verifyScript(self, transaction):
        for txOut in transaction.outputs:
            script = txOut.script
            if script == None or len(script) == 0:
                return False
            if txOut.hasExtScript():
                if len(script) < Config.getIntValue('EXTENSION_SCRIPT_LEN'):
                    return False
                if script[0] != Config.getIntValue('EXTENSION_SCRIPT_VERSION'):
                    return False
            else:
                if len(script) > Config.getIntValue('SCRIPT_LEN'):
                    return False
                if script[0] != Config.getIntValue('SCRIPT_VERSION', False):
                    return False
                    
                if script[1] == Opcodes.alias('MERGE', True):
                    if len(script) != Config.getIntValue('SCRIPT_MERGE_LEN'):
                        return False
                elif script[1] == Opcodes.alias('CHECKMULTISIGVERIFY', True):
                    if len(script) != Config.getIntValue('SCRIPT_MULTISIG_LEN'):
                        return False
                elif script[1] == Opcodes.alias('CHECKATOMICSWAPVERIFY', True):
                    if len(script) != Config.getIntValue('SCRIPT_ATOMIC_SWAP_LEN'):
                        return False
                elif script[1] == Opcodes.alias('CHECKATOMICSWAPLOCKVERIFY', True):
                    if len(script) != Config.getIntValue('SCRIPT_ATOMIC_SWAP_LEN'):
                        return False
                else:
                    if script[1] != Opcodes.alias('DUP1'):
                        return False
                    if script[2] != Opcodes.alias('PUBADDR', True):
                        return False
                    if script[3] != Opcodes.alias('ADDRESS'):
                        return False
                    if script[4] != Opcodes.alias('EQ'):
                        return False
                    if script[5] != Opcodes.alias('VERIFY', True):
                        return False
                    if script[6] != Opcodes.alias('CHECKSIGVERIFY', True):
                        return False
        return True

    def verifyAddress(self, transaction):
        for txOut in transaction.outputs:
            address = txOut.address
            if address == None or len(address) != Config.getIntValue('ADDRESS_LEN'):
                return False
            if txOut.hasExtScript():
                if UXTO.getUnspentTransactionScript(address) == None:
                    outpointBytes = bytearray()
                    for inputs in transaction.inputs:
                        outpoint = inputs.outpoint
                        outpointBytes.extend(outpoint.serialize())
                        
                    if address != Crypto.generateAddress(outpointBytes):
                        return False
                else: 
                    #contract exists and address is not available
                    return False
        return True
    
    def verifyExtraData(self, transaction):
        for txOut in transaction.outputs:
            extraData = txOut.extraData
            if txOut.hasExtScript():
                continue
            elif (txOut.isMultiSig() or txOut.isAtomicSwap()) and not txOut.isAtomicLock():
                if not isinstance(extraData, int):
                    return False
            elif extraData != None and len(extraData) > 0:
                return False
        return True

    '''
        The transaction size in bytes is less than TRANSACTION_SIZE_LIMIT
    '''
    def verifyTransactionSizeLimit(self, transaction):
        return True
    
    '''
        For each input, if the referenced output transaction is coinbase (i.e. only 1 input, with hash=0, n=-1), 
        it must have at least COINBASE_MATURITY (100) confirmations; else reject this transaction
    '''
    def verifyCoinbaseMaturity(self, transaction):
        for txIn in transaction.inputs:
            coin = UXTO.getUnspentTransactionCoin(txIn.outpoint)
            if coin.isCoinbase():
                chainHeadIndexBlock = Chain.getChain().getChainHeadIndexBlock()
                if Config.getIntValue('COINBASE_MATURITY') > chainHeadIndexBlock.height - coin.height:
                    return False
        return True
    
    '''
        For each input, if the referenced output does not exist (e.g. never existed or has already been spent), reject this transaction[6]
    '''
    def verifyUxtoReferencedOutput(self, transaction):
        for txIn in transaction.inputs:
            outpoint = txIn.outpoint
            if not UXTO.hasUnspentTransactionCoin(outpoint):
                return False
            return True
    
    '''
        Using the referenced output transactions to get input values, check that each input value, as well as the sum, are in the allowed range of values 
        (less than 21m coins, more than 0)
    '''
    def verifyAllowedInputValueRange(self, transaction):
        inputValueTotal = 0
        for txIn in transaction.inputs:
            coin = UXTO.getUnspentTransactionCoin(txIn.outpoint)
            txOut = coin.output
            if txOut.hasExtScript():
                if txOut.value < 0:
                    return False
            elif txOut.value <= 0:
                return False
            inputValueTotal += txOut.value
            
        '''
            Check coin supply limit
        '''
        coinSupplyLimit = Config.getIntValue('COIN_SUPPLY_LIMIT')
        if coinSupplyLimit > 0:
            if inputValueTotal > coinSupplyLimit:
                return False
        return True
    
    '''
        Reject if the sum of input values < sum of output values
        Reject if transaction fee (defined as sum of input values minus sum of output values) would be too low to get into an empty block
    '''
    def verifySumInputOutputValues(self, transaction):
        inputValueTotal = 0
        for txIn in transaction.inputs:
            coin = UXTO.getUnspentTransactionCoin(txIn.outpoint)
            txOut = coin.output
            inputValueTotal += txOut.value
        outputValueTotal = 0
        for txOut in transaction.outputs:
            outputValueTotal += txOut.value
        if inputValueTotal < outputValueTotal:
            return False
        if inputValueTotal - outputValueTotal <= 0:
            return False
        return True
    
    '''
        Each output value, as well as the total, must be within the allowed range of values (less than 21m coins, more than 0)
    '''
    def verifyAllowedOutputValueRange(self, transaction):
        outputValueTotal = 0
        for txOut in transaction.outputs:
            if txOut.hasExtScript():
                if txOut.value < 0:
                    return False
            elif txOut.value <= 0:
                return False
            outputValueTotal += txOut.value
            
        '''
            Check coin supply limit
        '''
        coinSupplyLimit = Config.getIntValue('COIN_SUPPLY_LIMIT')
        if coinSupplyLimit > 0:
            if outputValueTotal > coinSupplyLimit:
                return False
        return True
    
    '''
        None of the inputs have hash=0, N=-1 (coinbase transactions should not be relayed)
    '''
    def verifyInputsNonCoinbase(self, transaction):
        for txIn in transaction.inputs:
            if txIn.isCoinbase():
                return False 
        return True
    
    '''
        A valid transaction requires at least 100 bytes. If it's any less, the transaction is not valid
    '''
    def verifyTransactionRequiredSize(self, transaction):
        if not len(transaction.serialize()) >= 100:
            return False
        return True
    
    '''
        For each input, if the referenced output exists in any other tx in the pool, reject this transaction.[5]
    '''
    def verifyTxOutputDuplicateInPool(self, transaction):
        for txIn in transaction.inputs:
            outpoint = txIn.outpoint
            for txId in MemoryPool.getMemoryPool():
                tx = MemoryPool.getTransactionById(txId)
                for i in tx.inputs:
                    if outpoint == i.outpoint:
                        return False
        return True
    
    '''
        Reject if we already have matching tx in the pool
    '''
    def verifyTransactionDuplicateInPool(self, transaction):
        txId = transaction.hash()
        if txId in MemoryPool.getMemoryPool():
            return False
        return True
        
    '''
        The unlocking scripts for each input must validate against the corresponding output locking scripts
    '''
    def verifyUnlockingScripts(self, transaction):
        for txIn in transaction.inputs:
            coin = UXTO.getUnspentTransactionCoin(txIn.outpoint)
            txOut = coin.output
            #Standard transactions and contract call
            if not RVM.run(transaction, txIn, txOut):
                return False
        for txOut in transaction.outputs:
            if txOut.hasExtScript():
                #Deploy contract
                if not RVM.run(transaction, None, txOut, deploy=True):
                    return False
            elif UXTO.getUnspentTransactionScript(txOut.address) != None:
                #Send value to contract
                if not RVM.run(transaction, None, txOut, deploy=True):
                    return False
        return True
