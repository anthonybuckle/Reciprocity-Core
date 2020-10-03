from unittest import TestCase, main
from recip import recipcli

class test_Contract(TestCase):

    def test_WatchContracts(self):
        command = 'WatchContracts'
        parameters = []

        recipcli.handleCommand(command, parameters)

    def test_DeleteContracts(self):
        command = 'DeleteContracts'
        parameters = []

        recipcli.handleCommand(command, parameters)

    def test_GetContracts(self):
        command = 'GetContracts'
        parameters = []  

        recipcli.handleCommand(command, parameters)

if __name__ == '__main__':
    main()