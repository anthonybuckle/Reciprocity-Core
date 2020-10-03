from recip.core.Contract import Contract
from recip.util import Config
import json

class Contracts:
    contracts = []
    with open(Config.getValue('CONTRACTS_DIR')) as _contracts:  
        contractsJson = json.load(_contracts)
        for contractJson in contractsJson:
            _contract = Contract()
            _contract.deserialize(contractJson)
            contracts.append(_contract)
        
def getContracts():
    return Contracts.contracts
    
def getContractByAddress(address):
    for contract in Contracts.contracts:
        if address == contract.address:
            return contract
    return None
    
def addContract(contract, save=True):
    if not contract in Contracts.contracts:
        Contracts.contracts.append(contract)
        if save:
            writeContracts()
        return True
    else:
        return False
    
def removeContract(address, save=True):
    contract = getContractByAddress(address)
    if contract != None:
        Contracts.contracts.remove(contract)
        if save:
            writeContracts()
        return True
    else:
        return False
        
def writeContracts():
    _contracts = []
    for contract in Contracts.contracts:
        _contracts.append(contract.serialize())
    with open(Config.getValue('CONTRACTS_DIR'), 'w') as contract:  
        json.dump(_contracts, contract, indent=2, sort_keys=False)