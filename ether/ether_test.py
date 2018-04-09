import json
from binascii import hexlify
from time import sleep

from solc import compile_source
from uuid import uuid4
from web3 import Web3, IPCProvider, personal
from web3.contract import ConciseContract

# TODO: !!!!! TURN THIS FILE INTO TEST SUITE USING GETH_KEEPER !!!!!

# To use correctly install python3 and set as interpreter
# Install geth with the rinkeby test network and pip install web3
# Fund your rinkeby wallet by going to rinkeby.faucet.io

# Start up the geth node on the rinkeby test network as well as IPC protocol (enabling admin and personal api)
# with the following command:     geth --rinkeby ipc --ipcapi admin,eth,miner,personal 2>>./rinkebyEth.log

# Steps if you want to practice on the console:
# In another terminal set a symbolic link to the geth.ipc file:
#    ln -sf <path/to/rinkeby/geth.ipc/file> <path/to/Ethereum/directory>/geth.ipc


# TODO: should read in from a config file on initialize

IPC_LOCATION = '/Users/jordan/Library/Ethereum/rinkeby/geth.ipc'


class EtherManager(object):
    def __init__(self):
        # TODO: remove when moving to main ethereum network
        from web3.middleware import geth_poa_middleware
        self._w3 = Web3(IPCProvider(IPC_LOCATION))
        # Apply the 'extraData' formatting patch for working on rinkeby
        self._w3.middleware_stack.inject(geth_poa_middleware, layer=0)

    def create_account(self):
        """ Creates an ethereum account and returns the account number and private key

        :return: (acct_number, private_key)
        """
        private_key = str(uuid4())
        address = self._w3.personal.newAccount(private_key)
        return address, private_key

    def get_accounts(self):
        """ Returns an array of all account hashes

        :return: [<acct_hashes>]
        """
        return self._w3.personal.listAccounts

    def create_contract(self):
        """ Creates a simple contract and returns the contract address

        :return: String giving the address of the contract
        """
        # TODO: make this configurable with different parameters for a custom contract
        # TODO: this will need to take a gas price and the hash of the issuer's account
        contract_source_code = '''
        pragma solidity ^0.4.0;

        contract mortal {
            /* Define variable owner of the type address*/
            address owner;
        
            /* this function is executed at initialization and sets the owner of the contract */
            function mortal() { owner = msg.sender; }
        
            /* Function to recover the funds on the contract */
            function kill() { if (msg.sender == owner) suicide(owner); }
            
            function getOwner() constant returns (string) {
                return "owner";
            }
        }
        
        contract greeter is mortal {
            /* define variable greeting of the type string */
            string greeting;
            
            /* this runs when the contract is executed */
            function greeter(string _greeting) public {
                greeting = _greeting;
            }
        
            /* main function */
            function greet() constant returns (string) {
                return greeting;
            }
        }
        '''
        compiled_sol = compile_source(contract_source_code)  # Compiled source code
        print('compiled_sol is {0}'.format(str(compiled_sol)))

        # TODO: need db table storing components of the contract binary interface !!!!!
        contract_interface = compiled_sol['<stdin>:greeter']

        # TODO: remove this debugging code
        for key in contract_interface:
            print('key: {0}, value: {1}'.format(key, contract_interface[key]))

        # TODO: need to lock and then unlock the account to transact
        # Instantiate, deploy, and get the transaction hash of the contract
        self._w3.personal.unlockAccount(self._w3.eth.accounts[0], 'jhensley1234', duration=20)
        contract = self._w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
        tx_hash = contract.constructor('test').transact({'from': self._w3.eth.accounts[0], 'gasPrice': 1000000000})
        print('hash: {0}'.format(hexlify(tx_hash)))
        sleep(30)
        # Get tx receipt to get contract address and get the contract
        tx_receipt = self._w3.eth.getTransactionReceipt(tx_hash)
        print('trans_receipt: {0}'.format(tx_receipt))
        contract_address = tx_receipt['contractAddress']
        contract_instance = self._w3.eth.contract(abi=contract_interface['abi'], address=contract_address,
                                                  ContractFactoryClass=ConciseContract)

        # Getters + Setters for web3.eth.contract object
        print('Contract value: {}'.format(contract_instance.greet()))
        print('Setting value to: jordan')
        print('Contract value: {}'.format(contract_instance.greet()))
        print('KILLING CONTRACT')
        contract_instance.kill()
        self._w3.personal.lockAccount(self._w3.eth.accounts[0])

    def get_trans_count(self):
        return self._w3.eth.getTransactionCount(self._w3.eth.accounts[0])

    def get_transaction_receipt(self):
        trans_hash = self._w3.eth.getTransactionFromBlock(self._w3.eth.defaultBlock, 0)['hash']
        print('hash: {0}'.format(trans_hash))
        return self._w3.eth.getTransactionReceipt(trans_hash)

    def get_temp_trans(self):
        return self._w3.eth.getTransactionReceipt('0x7f7ebfa8838a585175c426b9d158fbaaa585c67f78afcec6bf47a2c81562c00f')

    def contract_test(self):
        contract_source_code = '''
                pragma solidity ^0.4.0;

                contract mortal {
                    /* Define variable owner of the type address*/
                    address owner;

                    /* this function is executed at initialization and sets the owner of the contract */
                    function mortal() { owner = msg.sender; }

                    /* Function to recover the funds on the contract */
                    function kill() { if (msg.sender == owner) suicide(owner); }
                }

                contract greeter is mortal {
                    /* define variable greeting of the type string */
                    string greeting;

                    /* this runs when the contract is executed */
                    function greeter(string _greeting) public {
                        greeting = _greeting;
                    }

                    /* main function */
                    function greet() constant returns (string) {
                        return greeting;
                    }
                }
                '''
        compiled_sol = compile_source(contract_source_code)  # Compiled source code
        print('compiled_sol is {0}'.format(str(compiled_sol)))

        # TODO: need db table storing components of the contract binary interface !!!!!
        contract_interface = compiled_sol['<stdin>:greeter']

        # Get tx receipt to get contract address and get the contract
        tx_receipt = self._w3.eth.getTransactionReceipt('0x0afc066b28dd8a9f5b014ef4eec16d6eacaa09de5175a2f0c726fd5ffeeaf84c')
        print('trans_receipt: {0}'.format(tx_receipt))
        contract_address = tx_receipt['contractAddress']
        contract_instance = self._w3.eth.contract(abi=contract_interface['abi'], address=contract_address,
                                                  ContractFactoryClass=ConciseContract)

        # Getters + Setters for web3.eth.contract object
        print('Contract value: {}'.format(contract_instance.greet()))
        print('Setting value to: jordan')
        print('Contract value: {}'.format(contract_instance.owner))
        print('KILLING CONTRACT')
        contract_instance.kill()

    def get_peers(self):
        return self._w3.admin.peers

    def get_receipt(self):
        return self._w3.eth.getTransactionReceipt('0x0afc066b28dd8a9f5b014ef4eec16d6eacaa09de5175a2f0c726fd5ffeeaf84c')

    def get_transactions(self):
        transactions = []
        blockNum = self._w3.eth.blockNumber
        for i in range(blockNum):
            block = self._w3.eth.getBlock(i, full_transactions=True)
            for trans in block['transactions']:
                if trans['from'] == self._w3.eth.accounts[0]:
                    transactions.append(trans)
        return transactions

    def get_trans(self):
        return self._w3.eth.getTransaction('0xfb8149499d093164c66d314f14d6abfd6f6937c630b39cd4285c91506f57eb88')


if __name__ == '__main__':
    em = EtherManager()
    print(em.get_accounts())
    # acct_num, priv_key = em.create_account()
    # print('CREATING CONTRACT!!!')
    # em.create_contract()
    # print('CONTRACT COMPLETED')
    # print('account: {0}, priv_key: {1}'.format(acct_num, priv_key))
    # print(em.get_accounts())

    # print('trans_Count: {0}'.format(em.get_trans_count()))
    # data = em.get_transaction_receipt()
    # for key, val in data.items():
    #     print('key: {0}, val: {1}'.format(key, val))
    # print('------------------------------------------------------')
    # # print(em.get_receipt())
    #
    # trans = em.get_transactions()
    # for trans in trans:
    #     print('trans: {0}'.format(trans))

    # trans = em.get_trans()
    # for key, val in trans.items():
    #     print('{0}: {1}'.format(key, val))

    em.create_contract()




