from recip.core.Log import Log as RVMLog
from recip.core.Output import Output
from recip.storage import PersistentStorage
from recip.storage import UXTO
from recip.vm import Opcodes
from recip.vm import Script
from copy import copy
from recip.util import Address
from recip.util import Chain
from recip.util import Config
from recip.util import Crypto
from recip.util import DataType
import math

class RVM:
    def __init__(self, transaction, _input, output, readOnly, deploy, localTx):
        self.transaction = transaction
        self.input = _input
        self.output = output
        
        self.persistentStorageKey = output.address
        self.origin = output.address

        self.gasRemaining = self.transaction.gasLimit
        
        self.chainHeadBlock = Chain.getChain().getChainHeadBlock()
        self.chainHeadIndexBlock = Chain.getChain().getChainHeadIndexBlock()

        self.code = bytearray()
        self.data = bytearray()
        self.pc = None
        self.currOpcode = None
        
        self.stack = []
        self.memory = bytearray()
        
        self.JUMPDEST = Opcodes.alias('JUMPDEST')
        
        self.readOnly = readOnly
        self.deploy = deploy
        self.localTx = localTx
        self.merge = False

        self.override = not output.hasExtScript()

        self.overrideAddress = None
        self.overrideScript = None
        self.overrideValue = None

        self.invalid = False
        self.logs = []
        
        self.initialize()
    
    def initialize(self):
        self.code = self.output.script[1:]
        parameters = []
        if self.deploy:
            parameters = [] if self.output.extraData == None else self.output.extraData
        else:
            if self.output.hasExtScript():
                parameters.extend(self.input.witness[3:])
            else:
                self.stack.extend(self.input.witness)
        methodHash = False if self.deploy else True
        for parameter in parameters:
            if not isinstance(parameter, bytes):
                try:
                    if methodHash:
                        parameter = DataType.fromHex(parameter)
                        parameter = DataType.serialize(parameter)
                        methodHash = False
                    else:
                        parameter = DataType.asInt(parameter)
                except ValueError:
                    try:
                        parameter = DataType.fromHex(parameter)
                        parameter = DataType.serialize(parameter)
                    except ValueError:
                        parameter = Address.toAddressBytes(parameter)
            if self.deploy:
                self.code += DataType.zeroFillArray(parameter, 32)
            else:
                if len(self.data) == 0:
                    self.data += parameter
                else:
                    self.data += DataType.zeroFillArray(parameter, 32)
        if len(self.data) > 0 and len(self.data) < 32:
            fillLen = 32 - len(self.data)
            self.data.extend(fillLen * b'\x00')
        
    def step(self, step=1):
        self.pc += step
    
    def pop(self):
        return self.stack.pop()
    
    def popAsInt(self):
        return DataType.bytesToInt(self.pop())
    
    def expandMemory(self, offset, length):
        size = offset + length
        if size > len(self.memory):
            expandSize = size - len(self.memory)
            self.memory.extend(b'\x00' * expandSize)
    
    def execute(self):
        success = False
        try:
            self.pc = 0
            while self.pc < len(self.code):
                element = self.code[self.pc]
                self.currOpcode = Opcodes.fetch(element, self.override)
                self.gasRemaining -= self.currOpcode.gas
                print(self.currOpcode.method, self.currOpcode.code, self.pc, self.gasRemaining)
                if self.gasRemaining >= 0:
                    method = getattr(self, self.currOpcode.method)
                    method()
                    self.step()
                else:
                    self.pc = len(self.code)
                    self.invalid = True
            if self.invalid:
                success = False
            else:
                if self.output.hasExtScript() or self.merge:
                    _address = self.output.address if self.overrideAddress == None else self.overrideAddress
                    _script = self.output.script if self.overrideScript == None else self.overrideScript
                    _value = self.output.value if self.overrideValue == None else self.overrideValue
                    if self.deploy and not self.merge:
                        script = bytearray()
                        script.append(Config.getIntValue("EXTENSION_SCRIPT_VERSION"))
                        script.extend(_script)
                        _script = DataType.serialize(script)
                    if self.deploy or self.merge or self.localTx:
                        # Output will be stored in the blockchain and not the UXTO
                        self.output.store = False
                        self.transaction.addInternalOutput(_address, _script, _value)
                self.transaction.gasRemaining = self.gasRemaining
                success = True
            if len(self.logs) > 0:
                key = self.persistentStorageKey + self.transaction.hash()
                PersistentStorage.add(key, self.logs, True)
        finally:
            if not self.readOnly:
                if success:
                    PersistentStorage.commit(self.persistentStorageKey)
                else:
                    PersistentStorage.rollback(self.persistentStorageKey)
        return success

    @staticmethod
    def run(transaction, _input, output, readOnly=False, deploy=False, localTx=False):
        vm = RVM(transaction, _input, output, readOnly, deploy, localTx)
        return vm.execute()

#################### RVM Extensions Begin ####################

    def sha256(self):
        data = self.pop()
        _hash = Crypto.generateHash(data, Config.getValue('SHA2_HASHING_ALGORITHM'))
        self.stack.append(_hash)

    def verify(self):
        valid = self.pop()
        if not valid:
            self.pc = len(self.code)
            self.invalid = True

    def checksig(self):
        public = self.pop()
        signature = self.pop()
        outputHash = self.transaction.hashOutput(self.input, self.output)
        self.stack.append(Crypto.verify(public, signature, outputHash))

    def checksigverify(self):
        self.checksig()
        self.verify()

    def _merge(self):
        unspentTransactionScript = UXTO.getUnspentTransactionScript(self.output.address)
        txOut = unspentTransactionScript.output
        self.overrideScript = txOut.script
        self.overrideValue = txOut.value + self.output.value
        self.merge = True

    def pubaddr(self):
        data = self.pop()
        _address = Crypto.generateAddress(data)
        self.stack.append(_address)

    def checkmultisig(self):
        outputHash = self.transaction.hashOutput(self.input, self.output)
        threshold = DataType.bytesToInt(self.output.extraData)
        match = 0
        publicKeys = self.input.witness[::2]
        multiSigAddressBytes = bytearray()
        for publicKey in publicKeys:
            multiSigAddressBytes.extend(publicKey)
        multiSigAddress = Crypto.generateAddress(multiSigAddressBytes)
        if multiSigAddress == self.output.address:
            signatures = self.input.witness[1::2]
            for public, signature in zip(publicKeys, signatures):
                if Crypto.verify(public, signature, outputHash):
                    match += 1
        self.stack.append(match >= threshold)

    def checkmultisigverify(self):
        self.checkmultisig()
        self.verify()

    def checkatomicswapverify(self):
        self.checkmultisig()
        self.verify()
        if self.invalid:
            self.checksig()
            self.verify()

    def checkatomicswaplockverify(self):
        self.checkmultisig()
        self.verify()
        if self.invalid:
            self.checksig()
            self.verify()

#################### RVM Extensions End ####################

    def stop(self):
        self.pc = len(self.code)
    
    def add(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(a + b)
    
    def mul(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(a * b)
    
    def sub(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(a - b)
    
    def div(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(a // b)
    
    def sdiv(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(a // b)
    
    def mod(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(a % b)
    
    def smod(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(a % b)
    
    def addmod(self):
        a = self.popAsInt()
        b = self.popAsInt()
        nItem = self.pop()
        self.stack.append(((a + b) % nItem))

    def mulmod(self):
        a = self.popAsInt()
        b = self.popAsInt()
        nItem = self.pop()
        self.stack.append(((a * b) % nItem))
    
    def exp(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(a ** b)
    
    def signextend(self):
        b = self.popAsInt()
        a = self.popAsInt()
        sign_bit = 1 << (b - 1)
        value = (a & (sign_bit - 1)) - (a & sign_bit)
        self.stack.append(value)
    
    def lt(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(1 if a < b else 0)
    
    def gt(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(1 if a > b else 0)
    
    def slt(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(a < b)
    
    def sgt(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(a > b)
    
    def eq(self):
        a = self.popAsInt()
        b = self.popAsInt()
        print('a', a, b)
        self.stack.append(1 if a == b else 0)
    
    def iszero(self):
        a = self.popAsInt()
        self.stack.append(1 if a == 0 else 0)
    
    def _and(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(a & b)
    
    def _or(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(a | b)
    
    def xor(self):
        a = self.popAsInt()
        b = self.popAsInt()
        self.stack.append(a ^ b)
    
    def _not(self):
        a = self.pop()
        self.stack.append(not a)
    
    def byte(self):
        a = self.popAsInt()
        b = self.pop()
        self.stack.append((b >> (a * 8)) & 0xFF)
    
    def shl(self):
        length = self.popAsInt()
        value = self.popAsInt()
        if length >= 256:
            self.stack.append(0)
        else:
            value = (value * 2 ** length) % 2 ** 256
            self.stack.append(value)
    
    def shr(self):
        length = self.popAsInt()
        value = self.popAsInt()
        if length >= 256:
            self.stack.append(0)
        else:
            value = math.floor(value / 2 ** length)
            self.stack.append(value)
    
    def sar(self):
        length = self.popAsInt()
        value = self.popAsInt()
        if length >= 256:
            self.stack.append(0)
        else:
            value = math.floor(value / 2 ** length)
            self.stack.append(value)
    
    def sha3(self):
        offset = self.popAsInt()
        length = self.popAsInt()
        data = self.memory[offset:offset + length]
        print('memory', 'sha3', 'data', data, len(self.memory))
        _hash = Crypto.generateHash(data, Config.getValue('SHA3_HASHING_ALGORITHM'))
        print('memory', 'sha3', 'hash', _hash)
        self.stack.append(_hash)
    
    def address(self):
        address = self.output.address
        print('address', address)
        self.stack.append(address)
    
    def balance(self):
        address = self.pop()
        address = DataType.serialize(address)
        print('balance', address)
        unspentTransactionScript = UXTO.getUnspentTransactionScript(address)
        self.stack.append(unspentTransactionScript.output.value)
    
    def _origin(self):
        self.stack.append(self.origin)
    
    def caller(self):
        _caller = None
        if self.input == None:
            _caller = self.code[-21:]
        else:
            _caller = self.input.witness[2]
        self.stack.append(_caller)
    
    def callvalue(self):
        value = 0
        if self.deploy: 
            value = self.output.value
        else:
            contractAddress = self.output.address
            for txOut in self.transaction.outputs:
                if txOut.address == contractAddress:
                    value += txOut.value
        value = DataType.zeroFillArray(value, 32)
        self.stack.append(value)
    
    def calldataload(self):
        offset = self.popAsInt()
        data = self.data[offset:offset + 32]
        print('calldataload', data)
        self.stack.append(data)
    
    def calldatasize(self):
        length = len(self.data)
        self.stack.append(length)
    
    def calldatacopy(self):
        offset = self.popAsInt()
        destOffset = self.popAsInt()
        length = self.popAsInt()
        self.expandMemory(destOffset, length)
        self.memory[destOffset:destOffset + length] = self.data[offset:offset + length]
        print('memory', 'calldatacopy', self.data[offset:offset + length])
    
    def codesize(self):
        length = len(self.code)
        self.stack.append(length)
    
    def codecopy(self):
        destOffset = self.popAsInt()
        offset = self.popAsInt()
        length = self.popAsInt()
        items = self.code[offset:offset + length]
        self.expandMemory(destOffset, length)
        self.memory[destOffset:destOffset + length] = items
        print('memory', 'codecopy', items, len(items))
        
    def gasprice(self):
        gasPrice = self.transaction.gasPrice
        gasPrice = DataType.zeroFillArray(gasPrice, 32)
        self.stack.append(gasPrice)
    
    def extcodesize(self):
        address = self.pop()
        unspentTransactionScript = UXTO.getUnspentTransactionScript(address)
        txOut = unspentTransactionScript.output
        size = len(txOut.script)
        self.stack.append(size)
    
    def extcodecopy(self):
        address = self.pop()
        destOffset = self.popAsInt()
        offset = self.popAsInt()
        length = self.popAsInt()

        unspentTransactionScript = UXTO.getUnspentTransactionScript(address)
        txOut = unspentTransactionScript.output

        self.memory[destOffset:destOffset + length] = txOut.script[offset:offset + length]
    
    def returndatasize(self):
        pass

    def returndatacopy(self):
        pass

    def extcodehash(self):
        address = self.pop()

        unspentTransactionScript = UXTO.getUnspentTransactionScript(address)
        txOut = unspentTransactionScript.output
        script = txOut.script

        _hash = 0 if script == None else Crypto.generateHash(script, Config.getValue('SHA3_HASHING_ALGORITHM'))
        self.stack.append(_hash)
    
    def blockhash(self):
        blockHeight = self.popAsInt()
        _blockHash = Chain.getChain().getBlockHashByHeight(blockHeight)
        self.stack.append(_blockHash)
    
    def coinbase(self):
        transactions = self.chainHeadBlock.transactions
        coinbaseTx = transactions[0]
        coinbaseOutput = coinbaseTx.outputs[0]
        self.stack.append(coinbaseOutput.address)
    
    def timestamp(self):
        timestamp = self.chainHeadBlock.timestamp
        self.stack.append(timestamp)
    
    def number(self):
        height = self.chainHeadIndexBlock.height
        self.stack.append(height)
    
    def difficulty(self):
        bits = self.chainHeadBlock.bits
        self.stack.append(bits)
    
    def gaslimit(self):
        gasLimit = self.chainHeadBlock.gasLimit
        gasLimit = DataType.zeroFillArray(gasLimit, 32)
        self.stack.append(gasLimit)

    def chainid(self):
        pass

    def selfbalance(self):
        pass
    
    def _pop(self):
        self.pop()
    
    def mload(self):
        offset = self.popAsInt()
        value = self.memory[offset:offset + 32]
        self.expandMemory(offset, 32)
        print('memory', 'mload', value)
        self.stack.append(value)
    
    def mstore(self):
        offset = self.popAsInt()
        value = self.pop()
        self.expandMemory(offset, 32)
        self.memory[offset:offset + 32] = DataType.zeroFillArray(value, 32)
        print('memory', 'mstore', value, len(self.memory))
    
    def mstore8(self):
        offset = self.popAsInt()
        value = self.pop()
        self.expandMemory(offset, 32)
        self.memory[offset] = value & 0xFF
    
    def sload(self):
        PersistentStorage.dump()
        key = self.pop()
        key = self.persistentStorageKey + key
        value = PersistentStorage.get(key, True)
        if value == None:
            value = DataType.zeroFillArray(0, 32)
        self.stack.append(value)
    
    def sstore(self):
        key = self.pop()
        value = self.pop()
        print(key, value)
        key = self.persistentStorageKey + key
        PersistentStorage.add(key, value, True)
        PersistentStorage.dump()
    
    def jump(self):
        self.pc = self.popAsInt()
        if self.JUMPDEST != self.code[self.pc]:
            self.pc = len(self.code)
            self.invalid = True
    
    def jumpi(self):
        destination = self.popAsInt()
        cond = self.pop()
        if cond != 0:
            self.pc = DataType.asInt(destination, 16)
            if self.JUMPDEST != self.code[self.pc]:
                self.pc = len(self.code)
                self.invalid = True
                        
    def _pc(self):
        self.stack.append(self.pc)
    
    def msize(self):
        length = len(self.memory)
        print('memory', 'msize', length)
        self.stack.append(length)
    
    def gas(self):
        gasRemaining = self.gasRemaining
        gasRemaining = DataType.zeroFillArray(gasRemaining, 32)
        self.stack.append(gasRemaining)
    
    def jumpdest(self):
        pass

    def push(self):
        startIdx = self.pc + 1
        endIdx = startIdx + self.currOpcode.index
        items = self.code[startIdx:endIdx]
        self.step(len(items))
        print('push', items, len(items))
        self.stack.append(items)
    
    def dup(self):
        idx = self.currOpcode.index
        value = self.stack[-idx]
        valueClone = copy(value)
        self.stack.append(valueClone)
    
    def swap(self):
        idx = self.currOpcode.index
        a = self.stack[-1]
        b = self.stack[-idx]
        self.stack[-idx] = a
        self.stack[-1] = b
    
    def log(self):
        index = self.currOpcode.index
        offset = self.popAsInt()
        length = self.popAsInt()
        topics = []
        for idx in range(index):
            topics.append(self.pop())
        data = self.memory[offset:offset + length]
        log = RVMLog(self.output.address, data, topics)
        self.logs.append(log)
    
    def create(self):
        value = self.popAsInt()
        offset = self.popAsInt()
        length = self.popAsInt()
        address = self.memory[offset:offset + length].value(value)
    
    def call(self):
        gas = self.popAsInt()
        address = DataType.intToBytes(self.pop())
        value = self.popAsInt()
        argsOffset = self.popAsInt()
        argsLength = self.popAsInt()
        retOffset = self.popAsInt()
        retLength = self.popAsInt()

        self.transaction.addInternalOutput(address, Script.verifySignature(), value)

        _address = self.output.address
        _script = self.output.script
        _value = self.output.value - value
        self.transaction.addInternalOutput(_address, _script, _value)
        
        #self.memory[retOffset:retOffset + retLength] = self.memory[argsOffset:argsOffset + argsLength]
        self.stack.append(1)
    
    def callcode(self):
        gas = self.popAsInt()
        address = self.pop()
        value = self.popAsInt()
        argsOffset = self.popAsInt()
        argsLength = self.popAsInt()
        retOffset = self.popAsInt()
        retLength = self.popAsInt()
        self.memory[retOffset:retOffset + retLength] = self.memory[argsOffset:argsOffset + argsLength]
    
    def _return(self):
        offset = self.popAsInt()
        length = self.popAsInt()
        print('memory', '_return', self.memory[offset:offset + length])
        self.overrideScript = self.memory[offset:offset + length]
        self.pc = len(self.code)
    
    def delegatecall(self):
        gas = self.popAsInt()
        address = self.pop()
        argsOffset = self.popAsInt()
        argsLength = self.popAsInt()
        retOffset = self.popAsInt()    
        retLength  = self.popAsInt()
        self.memory[retOffset:retOffset + retLength] = self.memory[argsOffset:argsOffset + argsLength]
    
    def create2(self):
        pass

    def staticcall(self):
        pass

    def revert(self):
        offset = self.popAsInt()
        length = self.popAsInt()
        self.overrideScript = self.memory[offset:offset + length]
        self.pc = len(self.code)
        self.invalid = True
    
    def _invalid(self):
        self.pc = len(self.code)
        self.invalid = True
    
    def selfdestruct(self):
        address = self.pop()
        self.overrideAddress = address
        self.overrideScript = Script.verifySignature()
        self.pc = len(self.code)