from unittest import TestCase, main
from recip import recipcli

class test_Transaction(TestCase):

    def test_SendTransaction(self):
        command = 'SendTransaction'
        parameters = []    

        recipcli.handleCommand(command, parameters)

if __name__ == '__main__':
    main()