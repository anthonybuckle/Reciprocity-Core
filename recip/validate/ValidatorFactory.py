from recip.validate.types.Block import Block
from recip.validate.types.Tx import Tx
from recip.validate import ValidatorType

def getInstance(vType):
        
    '''Validator Types'''
    if ValidatorType.BLOCK == vType:
        return Block()
    elif ValidatorType.TX == vType:
        return Tx()