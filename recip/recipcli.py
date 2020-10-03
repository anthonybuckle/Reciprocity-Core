#!/usr/bin/env python3

from Crypto.Hash import keccak
from argparse import ArgumentParser
from recip.util import JSONRPC
from recip.util import Http
from recip.util import DataType
import json

def main():
    parser = ArgumentParser(usage=
            'recipcli.py <command> [<parameter>, ...]                                                                                                                                                       \
                \n                                                                                                                                                                                          \
                \nReciprocity CLI - supported api commands:                                                                                                                                                 \
                \n                                                                                                                                                                                          \
                \nCommand                       Parameters                                                                                                      Description                                 \
                \nCreateAtomicSwapAccount       <public key>, ...                                                                                               Create a new atomic swap account            \
                \nCreateMultiSigAccount         <public key>, ...                                                                                               Create a new multisig account               \
                \nGetAccounts                                                                                                                                   List accounts and balances                  \
                \nGetNewAccount                                                                                                                                 Create new account                          \
                \nDeleteAccounts                <address>, ...                                                                                                  Remove an account                           \
                \nSendTransaction               <from address> <to address> <value> <gas limit> <gas price>                                                     Send a transaction                          \
                \nSendTransactionToMultiSig     <from address> <threshold> <to multisig address> <value> <gas limit> <gas price>                                Send a transaction to multisig address      \
                \nSendTransactionFromMultiSig   <from multisig address> <public key> <signature>, ... <threshold> <to address> <value> <gas limit> <gas price>  Send a transaction from multisig address    \
                \nSignMultiSigOutput            <multisig address> <threshold> <to address> <value> <gas limit> <gas price>                                     Sign a transaction output                   \
                \nGetMiningWorker               <address> <enabled>                                                                                             Create a mining worker                      \
                \nCreateAtomicSwapTx            <from address> <threshold> <to address> <value> <gas limit> <gas price>                                         Create atomic swap transaction              \
                \nSendAtomicSwapTx              <signedTx>                                                                                                      Send atomic swap transaction                \
                \nSignAtomicSwapTx              <unsignedTx>                                                                                                    Sign atomic swap transaction                \
                \nWatchContracts                <address>                                                                                                       Watch a contract                            \
                \nDeleteContracts               <address>, ...                                                                                                  Remove a contract                           \
                \nGetContracts                                                                                                                                  List contracts and balances                 \
                \nGetScriptLogs                 <from address> <contract address> <value> <gas limit> <gas price>                                               List script logs                            \
                \nDeployScript                  <from address> <script file> <parameters> <value> <gas limit> <gas price>                                       Deploy a script                             \
                \nDeployLocalScript             <from address> <script file> <parameters> <value> <gas limit> <gas price>                                       Deploy a local script                       \
                \nCallTxScript                  <from address> <contract address> <parameters> <value> <gas limit> <gas price>                                  Call a contract                             \
                \nCallLocalScript               <from address> <contract address> <parameters> <value> <gas limit> <gas price>                                  Call a local contract                       \
                \nWatchSideChain                <address>                                                                                                       Watch a side chain                          \
                \nGetSideChains                                                                                                                                 List sidechains                             \
                \nDeleteSideChains              <address>, ...                                                                                                  Remove a sidechain                          \
                \nDeploySideChain               <from address> <parameters> <value> <gas limit> <gas price>                                                     Deploy a sidechain                          \
                \nGetPeers                                                                                                                                      List peers                                  \
                \nAddPeers                      <hostname>, ...                                                                                                 Add a peer                                  \
                \nDeletePeers                   <hostname>, ...                                                                                                 Remove a peer'
    )
    parser.add_argument('command', help='api command', nargs='*')
    parser.add_argument('-n', '--host', type=str, default='localhost', help='Remote reciprocity host (default: localhost)')
    parser.add_argument('-p', '--port', type=int, default=8912, help='Remote reciprocity port (default: 8912)')

    args = parser.parse_args()
    commandLen = len(args.command)
    if commandLen == 0:
        parser.print_help()
        return
    command = args.command[0]
    parameters = None
    if commandLen > 1:
        parameters = args.command[1:]

    if args.host:
        hostname = args.host
        Http.setNodeHostname(hostname)

    if args.port:
        httpPort = args.port
        Http.setHttpPort(httpPort)
        
    handleCommand(command, parameters)

def handleCommand(command, parameters):
    id = 1
    commands = []
    if command == 'CreateAtomicSwapAccount':
        commands.append(JSONRPC.createMethodObject(command, parameters, id))
    elif command == 'CreateMultiSigAccount':
        commands.append(JSONRPC.createMethodObject(command, parameters, id))
    elif command == 'GetAccounts':
        commands.append(JSONRPC.createMethodObject(command, [], id))
    elif command == 'GetNewAccount':
        commands.append(JSONRPC.createMethodObject(command, [], id))
    elif command == 'DeleteAccounts':
        commands.append(JSONRPC.createMethodObject(command, parameters, id))
    elif command == 'SendTransaction':
        fromAddress = parameters[0]
        toAddress = parameters[1]
        value = DataType.asFloat(parameters[2])
        gasLimit = DataType.asInt(parameters[3])
        gasPrice = DataType.asFloat(parameters[4])
        params = {'fromAddress': fromAddress, 'toAddress': toAddress, 'value': value, 'gasLimit': gasLimit, 'gasPrice': gasPrice}
        commands.append(JSONRPC.createMethodObject(command, params, id))
    elif command == 'SendTransactionToMultiSig':
        fromAddress = parameters[0]
        threshold = DataType.asInt(parameters[1])
        toMultiSigAddress = parameters[2]
        value = DataType.asFloat(parameters[3])
        gasLimit = DataType.asInt(parameters[4])
        gasPrice = DataType.asFloat(parameters[5])
        params = {'fromAddress': fromAddress, 'threshold': threshold, 'toAddress': toMultiSigAddress, 'value': value, 'gasLimit': gasLimit, 'gasPrice': gasPrice}
        commands.append(JSONRPC.createMethodObject(command, params, id))
    elif command == 'SendTransactionFromMultiSig':
        fromAddress = parameters[0]
        publicKeys = [] 
        signatures = []
        idx = 0
        for parameter in parameters[1:-5]:
            if idx % 2 == 0:
                publicKeys.append(parameter)
            else:
                signatures.append(parameter)
            idx += 1
        threshold = DataType.asInt(parameters[-5])
        toAddress = parameters[-4]
        value = DataType.asFloat(parameters[-3])
        gasLimit = DataType.asInt(parameters[-2])
        gasPrice = DataType.asFloat(parameters[-1])
        params = {'fromAddress': fromAddress, 'publicKeys': publicKeys, 'signatures': signatures, 'threshold': threshold, 'toAddress': toAddress, 'value': value, 'gasLimit': gasLimit, 'gasPrice': gasPrice}
        commands.append(JSONRPC.createMethodObject(command, params, id))
    elif command == 'SignMultiSigOutput':
        multiSigAddress = parameters[0]
        threshold = DataType.asInt(parameters[1])
        toAddress = parameters[2]
        value = DataType.asFloat(parameters[3])
        gasLimit = DataType.asInt(parameters[4])
        gasPrice = DataType.asFloat(parameters[5])
        params = {'fromAddress': multiSigAddress, 'threshold': threshold, 'toAddress': toAddress, 'value': value, 'gasLimit': gasLimit, 'gasPrice': gasPrice}
        commands.append(JSONRPC.createMethodObject(command, params, id))
    elif command == 'GetMiningWorker':
        address = parameters[0]
        enabled = DataType.asBool(parameters[1])
        params = {'address': address, 'enabled': enabled}
        commands.append(JSONRPC.createMethodObject(command, params, id))
    elif command == 'CreateAtomicSwapTx':
        fromAddress = parameters[0]
        threshold = DataType.asInt(parameters[1])
        toAddress = parameters[2]
        value = DataType.asFloat(parameters[3])
        gasLimit = DataType.asInt(parameters[4])
        gasPrice = DataType.asFloat(parameters[5])
        params = {'fromAddress': fromAddress, 'threshold': threshold, 'toAddress': toAddress, 'value': value, 'gasLimit': gasLimit, 'gasPrice': gasPrice}
        commands.append(JSONRPC.createMethodObject(command, params, id))
    elif command == 'SendAtomicSwapTx':
        fromAddress = parameters[0]
        toAddress = parameters[1]
        value = DataType.asFloat(parameters[2])
        gasLimit = DataType.asInt(parameters[3])
        gasPrice = DataType.asFloat(parameters[4])
        params = {'fromAddress': fromAddress, 'toAddress': toAddress, 'value': value, 'gasLimit': gasLimit, 'gasPrice': gasPrice}
        commands.append(JSONRPC.createMethodObject(command, params, id))
    elif command == 'SignAtomicSwapTx':
        commands.append(JSONRPC.createMethodObject(command, parameters, id))
    elif command == 'WatchContracts':
        commands.append(JSONRPC.createMethodObject(command, parameters, id))
    elif command == 'DeleteContracts':
        commands.append(JSONRPC.createMethodObject(command, parameters, id))
    elif command == 'GetContracts':
        commands.append(JSONRPC.createMethodObject(command, [], id))
    elif command == 'GetScriptLogs':
        fromAddress = parameters[0]
        scriptAddress = parameters[1]
        value = DataType.asFloat(parameters[2])
        gasLimit = DataType.asInt(parameters[3])
        gasPrice = DataType.asFloat(parameters[4])
        params = {'fromAddress': fromAddress, 'script': scriptAddress, 'value': value, 'gasLimit': gasLimit, 'gasPrice': gasPrice}
        commands.append(JSONRPC.createMethodObject(command, params, id))
    elif command == 'DeployScript' or command == 'DeployLocalScript':
        fromAddress = parameters[0]
        with open(parameters[1], 'r') as scriptFile:
            script = scriptFile.read()
        _parameters = parameters[2:-3]
        value = DataType.asFloat(parameters[-3])
        gasLimit = DataType.asInt(parameters[-2])
        gasPrice = DataType.asFloat(parameters[-1])
        params = {'fromAddress': fromAddress, 'script': script, 'parameters': _parameters, 'value': value, 'gasLimit': gasLimit, 'gasPrice': gasPrice}
        commands.append(JSONRPC.createMethodObject(command, params, id))
    elif command == 'CallTxScript' or command == 'CallLocalScript':
        fromAddress = parameters[0]
        scriptAddress = parameters[1]
        _parameters = parameters[2:-3]
        if _parameters and len(_parameters) > 0:
            _parameters[0] = DataType.serialize(_parameters[0])
            hashFunction = keccak.new(data=_parameters[0], digest_bits=256)
            methodHash = hashFunction.hexdigest()
            _parameters[0] = methodHash[0:8]
        value = DataType.asFloat(parameters[-3])
        gasLimit = DataType.asInt(parameters[-2])
        gasPrice = DataType.asFloat(parameters[-1])
        params = {'fromAddress': fromAddress, 'script': scriptAddress, 'parameters': _parameters, 'value': value, 'gasLimit': gasLimit, 'gasPrice': gasPrice}
        commands.append(JSONRPC.createMethodObject(command, params, id))
    elif command == 'WatchSideChain':
        commands.append(JSONRPC.createMethodObject(command, parameters, id))
    elif command == 'DeleteSideChains':
        commands.append(JSONRPC.createMethodObject(command, parameters, id))
    elif command == 'GetSideChains':
        commands.append(JSONRPC.createMethodObject(command, [], id))
    elif command == 'DeploySideChain':
        fromAddress = parameters[0]
        parameters = parameters[1]
        value = DataType.asFloat(parameters[2])
        gasLimit = DataType.asInt(parameters[3])
        gasPrice = DataType.asFloat(parameters[4])
        params = {'fromAddress': fromAddress, 'parameters': parameters, 'value': value, 'gasLimit': gasLimit, 'gasPrice': gasPrice}
        commands.append(JSONRPC.createMethodObject(command, params, id))
    elif command == 'GetPeers':
        commands.append(JSONRPC.createMethodObject(command, [], id))
    elif command == 'AddPeers':
        commands.append(JSONRPC.createMethodObject(command, parameters, id))
    elif command == 'DeletePeers':
        commands.append(JSONRPC.createMethodObject(command, parameters, id))
    else:
        raise ValueError('Unsupported command: ' + command)
    
    url = '%s:%s' % (Http.getNodeHostname(), Http.getHttpPort())
    for cmd in commands:
        cmd = json.dumps(cmd)
        response = Http.send(url, cmd, doBasicAuth = True)
        if response == None or len(response) == 0:
            print('Empty response from ', url, 'request', cmd)
            continue
        response = json.loads(response)
        value = '\n'
        if 'result' in response:
            result = response['result']
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        for v in item.values():
                            value += ('%s\t' % v)
                        value += '\n'
                    else:
                        value += item
                        value += '\n'
            else:
                value += DataType.asString(result)
                value += '\n'
        elif 'error' in response:
            error = response['error']

            code = error['code']
            message = error['message']
            data = error['data']

            value += '%s %s %s' % (code, message, data)
            value += '\n'
        print(value)
        
if __name__ == '__main__':
    main()
