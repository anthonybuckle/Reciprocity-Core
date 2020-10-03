from recip.util import Config
from recip.util import Chain
from recip.util import DataType
import math

def getDifficultyFromBits(bits):
    target = getTargetFromBits(bits)
    genesisBits = Config.getIntValue('GENESIS_BLOCK_DIFFICULTY_BITS', 16)
    genesisTarget = getTargetFromBits(genesisBits)
    return DataType.asDecimal(genesisTarget) / DataType.asDecimal(target)

def getChainworkFromBits(previousChainWork, bits):
    difficulty = getDifficultyFromBits(bits)
    genesisChainwork = Config.getIntValue('GENESIS_BLOCK_CHAIN_WORK', 16)
    return math.floor(previousChainWork + difficulty * genesisChainwork)

def getTargetFromBits(bits):
    exponent = bits >> 24
    coefficient = bits & 0xffffff
    target = coefficient * 2 ** (8 * (exponent - 3))
    return target

def getBitsFromTarget(target):
    bitLength = target.bit_length() + 1
    size = (bitLength + 7) // 8
    bits = target >> 8 * (size - 3)
    bits |= size << 24
    return bits

def getBlockTime():
    if Config.getBoolValue('DGW3_ENABLED'):
        return Config.getIntValue('DGW3_BLOCK_TIME')
    else:
        return Config.getIntValue('BLOCK_TIME')

def getBlockRetargeting():
    if Config.getBoolValue('DGW3_ENABLED'):
        return Config.getIntValue('DGW3_BLOCK_RETARGETING')
    else:
        return Config.getIntValue('BLOCK_RETARGETING')

def getNewBlockBits(chainHeadBlock, chainHeadBlockHeight):
    newBlockBits = chainHeadBlock.bits
    if chainHeadBlockHeight > 0:
        blockRetargeting = getBlockRetargeting()
        if chainHeadBlockHeight % blockRetargeting == 0:
            retargetingStartBlock = chainHeadBlock
            retargeting = None
            index = 0
            while index < blockRetargeting:
                retargetingBlockTarget = getTargetFromBits(retargetingStartBlock.bits)
                if retargeting == None:
                    retargeting = retargetingBlockTarget
                if Config.getBoolValue('DGW3_ENABLED'):
                    if index > 0:
                        retargeting = (retargeting * index + retargetingBlockTarget) // (index + 1)    
                retargetingStartBlock = Chain.getChain().getBlockByHash(retargetingStartBlock.previousHash)
                index += 1
            blockIntervalTime = chainHeadBlock.timestamp - retargetingStartBlock.timestamp
            blockIntervalTime = math.ceil(blockIntervalTime)
            adjustedTarget = adjustTarget(retargeting, blockIntervalTime) 
            if adjustedTarget > getTargetFromBits(Config.getIntValue('GENESIS_BLOCK_DIFFICULTY_BITS', 16)):
                adjustedTarget = getTargetFromBits(Config.getIntValue('GENESIS_BLOCK_DIFFICULTY_BITS', 16))
            newBlockBits = getBitsFromTarget(adjustedTarget)
    return newBlockBits

def adjustTarget(retargeting, blockIntervalTime):
    targetTime = getBlockRetargeting() * getBlockTime()
    if Config.getBoolValue('DGW3_ENABLED'):
        if blockIntervalTime < targetTime // 3:
            blockIntervalTime = targetTime // 3
        if blockIntervalTime > targetTime * 3:
            blockIntervalTime = targetTime * 3
    adjustedTarget = retargeting * blockIntervalTime
    adjustedTarget = adjustedTarget // targetTime
    return adjustedTarget
