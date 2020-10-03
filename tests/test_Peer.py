from unittest import TestCase, main
from recip import recipcli

class test_Peer(TestCase):

    def test_GetPeers(self):
        command = 'GetPeers'
        parameters = []

        recipcli.handleCommand(command, parameters)

    def test_AddPeers(self):
        command = 'AddPeers'
        parameters = []

        recipcli.handleCommand(command, parameters)

    def test_DeletePeers(self):
        command = 'DeletePeers'
        parameters = []

        recipcli.handleCommand(command, parameters)

if __name__ == '__main__':
    main()