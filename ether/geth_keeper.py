from json import dumps, loads
from uuid import uuid4

from solc import compile_source
from web3 import Web3, IPCProvider

# To use correctly install python3 and set as interpreter
# Install geth with the rinkeby test network and pip install web3
# Fund your rinkeby wallet by going to rinkeby.faucet.io

# Start up the geth node on the rinkeby test network as well as IPC protocol (enabling admin and personal api)
# with the following command:     geth --rinkeby ipc --ipcapi admin,eth,miner,personal 2>>./rinkebyEth.log

# Steps if you want to practice on the console:
# In another terminal set a symbolic link to the geth.ipc file:
#    ln -sf <path/to/rinkeby/geth.ipc/file> <path/to/Ethereum/directory>/geth.ipc


# TODO: should read in from a config file on initialize
from web3.contract import ConciseContract

IPC_LOCATION = '/Users/jordan/Library/Ethereum/rinkeby/geth.ipc'

ACCT_UNLOCK_DUR = 5
MAX_GAS_PRICE = 500000000  # TODO: set back to 2000000000


class GethException(Exception):
    """ Class for representing exceptions thrown in the geth keeper

    **Attributes**:
        * exception: The exception's string value that was thrown
        * message: Optional message describing inpact
    """

    def __init__(self, exception, message=''):
        self.exception = exception
        self.message = message


class GethKeeper(object):
    def __init__(self):
        # TODO: remove middleware when moving to main ethereum network
        try:
            from web3.middleware import geth_poa_middleware
            self._w3 = Web3(IPCProvider(IPC_LOCATION))
            # Apply the 'extraData' formatting patch for working on the rinkeby network
            self._w3.middleware_stack.inject(geth_poa_middleware, layer=0)
        except Exception as e:
            raise GethException(str(e), 'Could not establish connection to node')

    def create_account(self):
        """ Creates an ethereum account and returns the account number and private key

        :return: (acct_number, private_key)
        """
        private_key = str(uuid4())
        try:
            address = self._w3.personal.newAccount(private_key)
            return address, private_key
        except Exception as e:
            raise GethException(str(e), 'Could not create account')

    # TODO: should gas_price not be a member?
    def issue_contract(self, issuer_acct_num, issuer_priv_key, issuer_name='', name='', desc='',
                       img_url='', num_tokes=0, transferable=False, gas_price=MAX_GAS_PRICE):
        """ Creates, compiles, and deploys a smart contract with the given attributes

        :param issuer_acct_num: The issuer's account hash
        :param issuer_priv_key: The issuer's private key
        :param issuer_name: The issuer's name to place in the contract - default: empty string
        :param name: The contract name - default: empty string
        :param desc: The contract description - default: empty string
        :param img_url: Contract image url as a string - default: empty string
        :param num_tokes: Contract's number of tokens - default: 0
        :param transferable: Boolean representing if the token is transferable - default: False
        :param gas_price: Willing gas price to pay - default: MAX_GAS_PRICE (2000000000)
        :return: Tuple - (transaction_hash, json_abi) as (string, string)
        """
        try:
            # Create code for non-transferable tokens
            trans_code = ''
            modifier = ''
            if not transferable:
                trans_code = """
                modifier onlyOwner {
                    require(msg.sender == owner);
                    _;   
                }
                """
                modifier = 'onlyOwner'

            # TODO: Have a different function to generate solidity code
            contract_source_code = """
                    pragma solidity ^0.4.0;
    
                    contract issuer_contract {{
                        // Address of the contract owner
                        address owner;
                        
                        // Contract members
                        string remaining_tokes;  // Holds the remaining # of tokens
                        string issuer_name;
                        string contract_name;
                        string contract_description;
                        string img_url;
                        int num_tokes;
    
                        // Constructor
                        function issuer_contract(string _in, string _cn, string _cd, string _iu, int _it) {{
                            // Set attributes
                            issuer_name = _in;
                            contract_name = _cn;
                            contract_description = _cd;
                            img_url = _iu;
                            remaining_tokes = _it;
                            num_tokes = _it;
                        
                            // Set the owner of the contract 
                            owner = msg.sender; 
                        }}
                        
                        {mod_def}
                        
                        // Function to get issuer_name
                        function get_issuer_name() constant returns (string) {{
                            return issuer_name;
                        }}
                        
                        // Function to get contract name
                        function get_contract_name() constant returns (string) {{
                            return contract_name;
                        }}
                        
                        // Function to get description
                        function get_description() constant returns (string) {{
                            return constract_description;
                        }}
                        
                        // Function to get image URL
                        function get_image_url() constant returns (string) {{
                            return img_url;
                        }}
                        
                        // Function to get the number of tokens
                        function get_num_tokens() constant returns (int) {{
                            return num_tokes;
                        }}
                        
                        // Function to get the remaining # of tokens
                        function get_remaining_tokens() constant returns (int) {{
                            return remaining_tokes;
                        }}
    
                        // Function to recover the funds on the contract
                        function kill() {{ 
                            if (msg.sender == owner) 
                                suicide(owner); 
                        }}
                    }} 
            """.format(mod_def=trans_code)
            # Compile the source code
            compiled_sol = compile_source(contract_source_code)
            contract_interface = compiled_sol['<stdin>:issuer_contract']

        except Exception as e:
            raise GethException(str(e), message='Could not compile smart contract')

        try:
            # Unlock the issuer's account to transact
            self._w3.personal.unlockAccount(issuer_acct_num, issuer_priv_key, duration=ACCT_UNLOCK_DUR)

            # Instantiate, deploy, and get the transaction hash of the contract
            contract = self._w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
            tx_hash = contract.constructor(issuer_name, name, desc, img_url, num_tokes).transact(
                {'from': issuer_acct_num, 'gasPrice': gas_price})

            # Lock the issuer's account back up and return the transaction hash
            self._w3.personal.lockAccount(issuer_acct_num)

            # Create the json string of the ABI and return
            abi_dict = {'abi': contract_interface['abi']}
            json_abi = dumps(abi_dict)
            return tx_hash, json_abi
        except Exception as e:
            raise GethException(str(e), message='Could not deploy smart contract')

    def check_contract_mine(self, tx_hash):
        """ Returns a contract address if the contract has been mined, None otherwise

        :param tx_hash: The transaction hash of the contract deployment
        :return: The contract address or None if it has yet to be mined
        """
        try:
            tx_receipt = self._w3.eth.getTransactionReceipt(tx_hash)
            if tx_receipt:
                return tx_receipt['contractAddress']
            return None
        except Exception as e:
            raise GethException(str(e), message='Could not check transaction receipt')

    def get_contract_instance(self, json_abi, contract_address):
        """ Returns an instance of the contract specified by the given abi at the given address

        This instance will contain all of the members and functions that are defined
        in the solidity code (ex. get_image_url())

        :param json_abi: The contract's ABI as a json string
        :param contract_address: The
        :return: An instance of the contract
        """
        try:
            abi_dict = loads(json_abi)
            return self._w3.eth.contract(abi=abi_dict['abi'], address=contract_address,
                                         ContractFactoryClass=ConciseContract)
        except Exception as e:
            raise GethException(str(e), message='Could not get contract instance')

    def claim_token(self):
        # TODO: implement
        # TODO: create a process to listen for send events
        # TODO: add event to smart contract to send token
        pass

    def get_users_tokens(self):
        # TODO: to get a user's tokens, we will have to query all of tokens monitored by Token
        pass