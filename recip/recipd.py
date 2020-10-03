#!/usr/bin/env python3

from argparse import ArgumentParser
from recip.network.SocketNode import SocketNode
from recip.network.HttpNode import HttpNode
from recip.util import Chain
from recip.util import Config
from recip.util import DataType
from recip.util import Network
from recip.util import Http
from recip.network import UPnP
import sys

def main():
    UPnP.init()
    Chain.init()
    
    parser = ArgumentParser(usage=
            'recipd.py <arguments> [<option>, ...]                                                       \
                \n                                                                                       \
                \nReciprocity Daemon - supported arguments:                                              \
                \n                                                                                       \
                \nArgument           Option          Description                                         \
                \n-s                 <port>          Service API port used by nodes (default: 8912)      \
                \n-n                 <port>          Communication port used by nodes (default: 8489)'
    )
    parser.add_argument('-s', '--service_port', type=int, default=8912, help='Service API port used by nodes (default: 8912)')
    parser.add_argument('-n', '--node_port', type=int, default=8489, help='Communication port used by nodes (default: 8489)')

    try:
        arguments = parser.parse_args()
        handleArguments(arguments)
    except:
        parser.print_help()
        return

def handleArguments(arguments):
    httpPort = Http.getHttpPort()
    socketPort = Network.getSocketPort()

    if arguments.service_port:
        httpPort = arguments.service_port
        Http.setHttpPort(httpPort)
    if arguments.node_port:
        socketPort = arguments.node_port
        Network.setSocketPort(socketPort)

    if Config.getBoolValue("ENABLE_HTTP_SERVICE"):
        httpNode = HttpNode(httpPort)
        httpNode.start()
        
    UPnP.addPortMapping(socketPort)
    
    socketNode = SocketNode(socketPort)
    socketNode.sync()
    socketNode.start()
    
if __name__ == '__main__':
    main()