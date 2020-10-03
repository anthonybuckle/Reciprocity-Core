from unittest import TestCase, main
from recip import recipcli

class test_Account(TestCase):

    def test_GetAccounts(self):
        command = 'GetAccounts'
        parameters = []

        recipcli.handleCommand(command, parameters)

    def test_GetNewAccount(self):
        command = 'GetNewAccount'
        parameters = []

        recipcli.handleCommand(command, parameters)

    def test_DeleteAccounts(self):
        command = 'DeleteAccounts'
        parameters = []

        recipcli.handleCommand(command, parameters)

if __name__ == '__main__':
    main()