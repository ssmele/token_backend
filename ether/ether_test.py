import json
from solc import compile_source
from uuid import uuid4
from web3 import Web3, IPCProvider, personal
from web3.contract import ConciseContract

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
        address = self._w3.personal.newAccount(private_key)[0]
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
        contract = self._w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
        tx_hash = contract.constructor('test').transact({'from': self._w3.eth.accounts[0], 'gas': 410000})

        # Get tx receipt to get contract address and get the contract
        tx_receipt = self._w3.eth.getTransactionReceipt(tx_hash)
        contract_address = tx_receipt['contractAddress']
        contract_instance = self._w3.eth.contract(abi=contract_interface['abi'], address=contract_address,
                                            ContractFactoryClass=ConciseContract)

        # Getters + Setters for web3.eth.contract object
        print('Contract value: {}'.format(contract_instance.greet()))
        print('Setting value to: jordan')
        contract_instance.setGreeting('jordan', transact={'from': self._w3.eth.accounts[0]})
        print('Contract value: {}'.format(contract_instance.greet()))
        contract_instance.kill()


if __name__ == '__main__':
    em = EtherManager()
    print(em.get_accounts())
    # em.create_account()
    em.create_contract()
    print(em.get_accounts())