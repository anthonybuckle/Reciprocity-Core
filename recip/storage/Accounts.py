from recip.core.Account import Account
from recip.util import Address
from recip.util import Config
from recip.util import DataType
from recip.util import Units
from recip.storage.Storage import Storage
import json

class Accounts:
    accounts = []
    with open(Config.getValue('WALLET_DIR')) as wallet:  
        accountsJson = json.load(wallet)
        for accountJson in accountsJson:
            account = Account("")
            account.deserialize(accountJson)
            accounts.append(account)

    indexDb = Config.getFilePath("CHAIN_DIRECTORY", "ACCOUNTS_INDEX_DB")
    balancesSubDb = Config.getValue("BALANCES_SUB_DB")
    localUxtoSubDb = Config.getValue("LOCAL_UXTO_SUB_DB")

    index = Storage(indexDb)
        
def getAccounts():
    return Accounts.accounts

def hasAddress(address):
    return getAccountByAddress(address) != None

def getConfirmedBalanceByAddress(address):
    confirmedBalanceBytes = Accounts.index.get(address, Accounts.balancesSubDb)
    return DataType.deserialize(confirmedBalanceBytes, DataType.INT, 0)

def addConfirmedBalanceByAddress(address, value):
    oldConfirmedBalance = getConfirmedBalanceByAddress(address)
    newConfirmedBalance = oldConfirmedBalance + value
    newConfirmedBalanceBytes = DataType.serialize(newConfirmedBalance)
    Accounts.index.set(address, newConfirmedBalanceBytes, Accounts.balancesSubDb)

def subtractConfirmedBalanceByAddress(address, value):
    oldConfirmedBalance = getConfirmedBalanceByAddress(address)
    newConfirmedBalance = oldConfirmedBalance - value
    newConfirmedBalanceBytes = DataType.serialize(newConfirmedBalance)
    Accounts.index.set(address, newConfirmedBalanceBytes, Accounts.balancesSubDb)

def addUnspentTransactionCoin(outpoint, coin):
    Accounts.index.set(outpoint.serialize(), coin.serialize(), Accounts.localUxtoSubDb)

def removeUnspentTransactionCoin(outpoint):
    Accounts.index.remove(outpoint.serialize(), Accounts.localUxtoSubDb)

def getAccountByAddress(address):
    for account in Accounts.accounts:
        if address == account.address:
            return account
    return None

def getAccountByPublic(public):
    for account in Accounts.accounts:
        if public == account.public:
            return account
    return None
    
def addAccount(account, save=True):
    if not account in Accounts.accounts:
        Accounts.accounts.append(account)
        if save:
            writeAccounts()
    
def removeAccount(address, save=True):
    account = getAccountByAddress(address)
    if account != None:
        Accounts.accounts.remove(account)
        if save:
            writeAccounts()
        return True
    else:
        return False
        
def writeAccounts():
    accountList = []
    for account in Accounts.accounts:
        accountList.append(account.serialize())
    with open(Config.getValue('WALLET_DIR'), 'w') as wallet:  
        json.dump(accountList, wallet, indent=2, sort_keys=False)
