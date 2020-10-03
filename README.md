
![Reciprocity Logo](https://github.com/anthonybuckle/Reciprocity-UI/blob/main/shared/img/reciprocity_logo.png)

Reciprocity-Core

Reciprocity is an experimental blockchain that supports transactions and limited smart contracts. I started this project in 2017 as a hobby. The primary goal of the project was to develop a skill set in another programming language and as a tool to learn core blockchain principles. My wife April helped design and created the reciprocity logo and wallet theme. I started experimenting with atomic swaps, side chains and multi-signatures transactions. I did not finish their implementation. To date reciprocity is not under development, so I have decided to release the code for others to gain value from my experiences.

Reciprocity uses port 8489 for peer communication and port 8912 for wallet json rpc requests.

My implementation is inspired by Bitcoin and Ethereum. It supports the following features and concepts:

* Limited smart contract support
* I provide an example erc20 token which executes in my virtual machine implementation
* P2P Node - Port 8489
* Full Block and Transaction verification
* Block Reorganization
* Orphaned Transactions
* Syncing of blocks and transactions with peers
* UXTO Set
* Segregated Witness - Stores witness signatures at the end of the transaction.
* Gospel P2P Protocol
* LMDB is used for storage
* ECDSA and Schnorr Public / Private Keys
* Proof of Work Mining - Uses a combination of blake2b512, sha512, whirlpool, ripemd160, sha256 hashing.
* Currency with an 8 coinbase block reward
* Merkle Trees
* Seed Peers
* JSON RPC - Port 8912
* RLP Serialization
* UPNP
* CLI
* Web, Desktop and Mobile Wallet
* Docker scripts
* MIT Licensed

Reciprocity requires the following:

* Requires Python3
* Requires python-ecdsa
* Requires ECPy
* Requires LMDB
* Requires js-sha3
* Requires PyCryptodome

You can run the following command to install all software requirements:

> python3 -m pip install -r requirements.txt

To setup reciprocity you may need to add it to your python path:

> . ./setenv.sh

> export PYTHONPATH=~/git/reciprocity:$PYTHONPATH

Reciprocity-UI can be found here: [Here](https://github.com/anthonybuckle/Reciprocity-UI)

Reciprocity Web Wallet Examples

1) Get accounts and balances:

![Accounts](https://github.com/anthonybuckle/Reciprocity-UI/blob/main/shared/img/Web-Accounts.png)

2) Start the mining process for blocks and transactions:

![Mining](https://github.com/anthonybuckle/Reciprocity-UI/blob/main/shared/img/Web-Mining.png)

4) Send a transaction

![Send Transaction](https://github.com/anthonybuckle/Reciprocity-UI/blob/main/shared/img/Web-Transaction1.png)

![Send Transaction](https://github.com/anthonybuckle/Reciprocity-UI/blob/main/shared/img/Web-Transaction2.png)

5) Deploy a smart erc20 token smart contract with an initial balance of 10000

![Deploy Contract](https://github.com/anthonybuckle/Reciprocity-UI/blob/main/shared/img/Web-Deploy1.png)

![Deploy Contract](https://github.com/anthonybuckle/Reciprocity-UI/blob/main/shared/img/Web-Deploy2.png)

![Contracts](https://github.com/anthonybuckle/Reciprocity-UI/blob/main/shared/img/Web-Contracts.png)

6) Call a erc20 smart contract method totalSupply(), which returns 10000 for the balance.

![Call Contract](https://github.com/anthonybuckle/Reciprocity-UI/blob/main/shared/img/Web-ContractCall.png)

Reciprocity CLI Examples
**Escape smart contract parameters with single quotes. For example, 'method()'

You can use recipcli.py to manually run commands against your node.

1) Get accounts and balances:

> ./recip/recipcli.py -n localhost GetAccounts

![Accounts](https://github.com/anthonybuckle/Reciprocity-UI/blob/main/shared/img/cli-accounts.png)

2) Start the mining process for blocks and transactions:

> ./recip/recipcli.py -n localhost GetMiningWorker 0x095ca22a93842270f13964dd990ab9c93db4187a true

![Mining](https://github.com/anthonybuckle/Reciprocity-UI/blob/main/shared/img/cli-mining.png)

3) Add a peer node

> ./recip/recipcli.py -n localhost AddPeers 192.168.0.28

4) Send a transaction

> ./recip/recipcli.py -n localhost SendTransaction 0x095ca22a93842270f13964dd990ab9c93db4187a 0x62e9879c3d6602d0f142d9733f3d04c6b793499e 100 21000 0.000000000000000001

![Send Transaction](https://github.com/anthonybuckle/Reciprocity-UI/blob/main/shared/img/cli-transaction.png)

5) Deploy a smart erc20 token smart contract

> ./recip/recipcli.py -n localhost DeployScript 0x095ca22a93842270f13964dd990ab9c93db4187a /Users/anthonybuckle/git/reciprocity/contracts/BasicToken.bin 10000 0 21000 0.000000000000000001

![Deploy Contract](https://github.com/anthonybuckle/Reciprocity-UI/blob/main/shared/img/cli-deploy.png)

6) Call a smart contract

> ./recip/recipcli.py -n localhost CallLocalScript 0x095ca22a93842270f13964dd990ab9c93db4187a 0x16f460aadc7ba20fece0176e07263bde330022300 'totalSupply()' 0 21000 0.000000000000000001

![Call Contract](https://github.com/anthonybuckle/Reciprocity-UI/blob/main/shared/img/cli-call%20contract.png)

Python Unit Testing are not fully implemented but here are some patterns to follow:

> python3 -m unittest tests.test_Account

> python3 -m unittest tests.test_Contract

> python3 -m unittest tests.test_Mining

> python3 -m unittest tests.test_Peer

> python3 -m unittest tests.test_Script

> python3 -m unittest tests.test_Transaction

> python3 -m unittest discover ../tests