from recip.network.messages.extensions.types.Account import Account
from recip.network.messages.extensions.types.AtomicSwap import AtomicSwap
from recip.network.messages.extensions.types.Chains import Chains
from recip.network.messages.extensions.types.Contract import Contract
from recip.network.messages.extensions.types.Mining import Mining
from recip.network.messages.extensions.types.Peer import Peer
from recip.network.messages.extensions.types.Script import Script
from recip.network.messages.extensions.types.Sidechain import Sidechain
from recip.network.messages.extensions.types.Transaction import Transaction
from recip.network.messages.extensions import ExtMessageType

def getInstance(msg):
    msgType = msg
    if isinstance(msg, dict):
        msgType = msg['method']
    
    '''Extension Messages Types'''
    if msgType in {
        ExtMessageType.GET_ACCOUNTS, ExtMessageType.GET_NEW_ACCOUNT, ExtMessageType.DELETE_ACCOUNTS,
        ExtMessageType.CREATE_MULTISIG_ACCOUNT, ExtMessageType.CREATE_ATOMIC_SWAP_ACCOUNT
    }:
        return Account()
    elif msgType in {ExtMessageType.WATCH_CONTRACTS, ExtMessageType.DELETE_CONTRACTS, ExtMessageType.GET_CONTRACTS}:
        return Contract()
    elif msgType in {
        ExtMessageType.DEPLOY_SCRIPT, ExtMessageType.DEPLOY_LOCAL_SCRIPT, 
        ExtMessageType.CALL_TX_SCRIPT, ExtMessageType.CALL_LOCAL_SCRIPT,
        ExtMessageType.GET_SCRIPT_LOGS
    }:
        return Script()
    elif msgType in {ExtMessageType.GET_MINING_WORKER}:
        return Mining()
    elif msgType in {ExtMessageType.CREATE_ATOMIC_SWAP_TX, ExtMessageType.SEND_ATOMIC_SWAP_TX, ExtMessageType.SIGN_ATOMIC_SWAP_TX}:
        return AtomicSwap()
    elif msgType in {ExtMessageType.GET_PEERS, ExtMessageType.ADD_PEERS, ExtMessageType.DELETE_PEERS}:
        return Peer()
    elif msgType in {ExtMessageType.SEND_TRANSACTION, 
        ExtMessageType.SEND_TRANSACTION_TO_MULTISIG, ExtMessageType.SEND_TRANSACTION_FROM_MULTISIG, 
        ExtMessageType.SIGN_MULTISIG_OUTPUT
    }:
        return Transaction()
    elif msgType in {ExtMessageType.WATCH_SIDECHAIN, ExtMessageType.GET_SIDECHAINS, ExtMessageType.DELETE_SIDECHAINS}:
        return Sidechain()
    elif msgType in {ExtMessageType.DEPLOY_SIDECHAIN}:
        return Chains()
