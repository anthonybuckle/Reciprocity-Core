from unittest import TestCase, main
from recip import recipcli

class test_Mining(TestCase):

    def test_GetMiningWorker(self):
        command = 'GetMiningWorker'
        parameters = []

        recipcli.handleCommand(command, parameters)

if __name__ == '__main__':
    main()