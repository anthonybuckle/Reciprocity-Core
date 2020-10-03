from unittest import TestCase, main
from recip import recipcli

class test_Script(TestCase):

    def test_DeployScript(self):
        command = 'DeployScript'
        parameters = []

        recipcli.handleCommand(command, parameters)

    def test_DeployLocalScript(self):
        command = 'DeployLocalScript'
        parameters = []

        recipcli.handleCommand(command, parameters)

    def test_CallTxScript(self):
        command = 'CallTxScript'
        parameters = []

        recipcli.handleCommand(command, parameters)

    def test_CallLocalScript(self):
        command = 'CallLocalScript'
        parameters = []

        recipcli.handleCommand(command, parameters)

if __name__ == '__main__':
    main()