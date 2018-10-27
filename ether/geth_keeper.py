import os
from binascii import hexlify, unhexlify
from datetime import datetime
from json import dumps, loads
from uuid import uuid4
from random import randint

from solc import compile_source
from web3 import Web3, IPCProvider
from web3.contract import ConciseContract
from ether.contract_source import CONTRACT

# To use correctly install python3 and set as interpreter
# Install geth with the rinkeby test network and pip install web3
# Fund your rinkeby wallet by going to rinkeby.faucet.io
# Start up the geth node on the rinkeby test network as well as IPC protocol (enabling admin and personal api)
# with the following command:     geth --rinkeby ipc --ipcapi admin,eth,miner,personal 2>>./rinkebyEth.log
# Steps if you want to practice on the console:
# In another terminal set a symbolic link to the geth.ipc file:
#    ln -sf <path/to/rinkeby/geth.ipc/file> <path/to/Ethereum/directory>/geth.ipc
# To run the node on the server:
#     geth --rinkeby --datadir=/usr/apps/Ethereum/rinkeby ipc --ipcapi admin,eth,miner,personal 2>>/usr/apps/EthLog.txt
# To run console on existing node:    geth --rinkeby --datadir=/usr/apps/Ethereum attach


# IPC_LOCATION = '/home/anna/.ethereum/rinkeby/geth.ipc'
# IPC_LOCATION = '/home/stone/.ethereum/rinkeby/geth.ipc'
from utils.utils import log_kv, LOG_ERROR

IPC_LOCATION = os.getenv('IPC_LOC', '/usr/apps/Ethereum/rinkeby/geth.ipc')

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
        log_kv(LOG_ERROR, {'error': self.message, 'exception': self.exception}, exception=True)


class MockGethKeeper(object):

    def create_account(self, *args, **kwargs):
        return 0, 123

    def issue_contract(self, *args, **kwargs):
        return hexlify(b'a2'), '{}'

    def check_contract_mine(self, *args, **kwargs):
        return True, True, 123

    def check_claim_mine(self, *args, **kwargs):
        return True, True

    def claim_token(self, *args, **kwargs):
        return hexlify(b'a2'), randint(0, MAX_GAS_PRICE)

    def get_users_token_id(self, *args, **kwargs):
        return -1

    def get_eth_balance(self, *args, **kwargs):
        #raise GethException('yeet', 'yeet')
        return 10


class GethKeeper(object):

    def __init__(self):
        # TODO: remove middleware when moving to main ethereum network
        try:
            from web3.middleware import geth_poa_middleware
            self._w3 = Web3(IPCProvider(IPC_LOCATION))

            # Apply the 'extraData' formatting patch for working on the rinkeby network
            self._w3.middleware_stack.inject(geth_poa_middleware, layer=0)

            # Set the root funding account
            self._root_acct = self._w3.toChecksumAddress('0xff95b24806e3d93afc628c4bb684fd245e9853e9')
            self._root_priv_key = 'jhensley1234'  # TODO: Fix this
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

    def issue_contract(self, issuer_acct_num, issuer_name='', name='', symbol='TOKE', desc='',
                       img_url='', num_tokes=0, code_reqs=None, date_reqs=None, loc_reqs=None,
                       tradable=False, gas_price=MAX_GAS_PRICE):
        """ Creates, compiles, and deploys a smart contract with the given attributes

        :param issuer_acct_num: The issuer's account hash
        :param issuer_name: The issuer's name to place in the contract - default: empty string
        :param name: The contract name - default: empty string
        :param symbol: The contract's symbol - default: 'TOKE'
        :param desc: The contract description - default: empty string
        :param img_url: Contract image url as a string - default: empty string
        :param num_tokes: Contract's number of tokens - default: 0
        :param code_reqs: Array of codes needed to claim the token - default: None
        :param date_reqs: Array of date ranges of when the token is available as [start_1, end_1, start_2, ...]
                          - default: None
        :param loc_reqs: Array of locations the token can be claimed at as [lat_1, long_1, rad_1, ...]
                          - default: None
        :param gas_price: Willing gas price to pay - default: MAX_GAS_PRICE (2000000000)
        :return: Tuple - (transaction_hash, json_abi) as (string, string)
        """
        code_reqs = [bytes(code, 'utf8') for code in code_reqs] if code_reqs else []
        date_reqs = [int(date) for date in date_reqs] if date_reqs else []
        loc_reqs = [int(loc * 1000000) for loc in loc_reqs] if loc_reqs else []

        try:
            # Compile the source code
            contract_source_code = CONTRACT
            compiled_sol = compile_source(contract_source_code)
            contract_interface = compiled_sol['<stdin>:issuer_contract']

        except Exception as e:
            raise GethException(str(e), message=str(e))

        try:
            # Normalize issuer account and unlock the root account
            issuer_acct_num = self._w3.toChecksumAddress(issuer_acct_num)
            self._w3.personal.unlockAccount(self._root_acct, self._root_priv_key, duration=ACCT_UNLOCK_DUR)

            # Instantiate, deploy, and get the transaction hash of the contract
            contract = self._w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])

            # Call the constructor of the contract
            tx_hash = contract.constructor(issuer_acct_num, issuer_name, name, symbol, desc, img_url,
                                           num_tokes, code_reqs, date_reqs, loc_reqs, tradable) \
                .transact({'from': self._root_acct, 'gasPrice': gas_price})

            # Lock the issuer's account back up and return the transaction hash
            self._w3.personal.lockAccount(self._root_acct)

            # Create the json string of the ABI and return
            abi_dict = {'abi': contract_interface['abi']}
            json_abi = dumps(abi_dict)
            return hexlify(tx_hash), json_abi
        except Exception as e:
            raise GethException(str(e), message=str(e))

    def check_contract_mine(self, tx_hash):
        """ Returns a contract address if the contract has been mined, None otherwise

        :param tx_hash: The transaction hash of the contract deployment
        :return: Tuple - (got_receipt, succeeded, contract_addr | None)
        """
        try:
            # Get the transaction receipt
            tx_hash = unhexlify(tx_hash)
            tx_receipt = self._w3.eth.getTransactionReceipt(tx_hash)
            if tx_receipt:
                # Return got_receipt, succeeded, and the contract address (None if failed)
                if tx_receipt['status'] == 0:
                    return True, False, None
                else:
                    return True, True, tx_receipt['contractAddress']
            return False, False, None
        except Exception as e:
            raise GethException(str(e), message='Could not check transaction receipt')

    def check_claim_mine(self, tx_hash):
        """ Returns if there is a receipt and if the transaction succeeded

        :param tx_hash: The transaction hash
        :return: Tuple - (got_receipt, did_succeed, receipt)
        """
        try:
            # Get the transaction receipt
            tx_hash = unhexlify(tx_hash)
            tx_receipt = self._w3.eth.getTransactionReceipt(tx_hash)
            if tx_receipt:
                # Return got_receipt, and succeeded
                return True, tx_receipt['status'] == 1, tx_receipt
            return False, False, None
        except Exception as e:
            raise GethException(str(e), message='Could not check transaction receipt')

    def get_contract_instance(self, json_abi, contract_address):
        """ Returns a read-only instance of the contract specified by the given abi at the given address

        This instance will contain all of the members and functions that are defined
        in the solidity code (ex. get_image_url())

        :param json_abi: The contract's ABI as a json string
        :param contract_address: The
        :return: An instance of the contract
        """
        try:
            contract_address = self._w3.toChecksumAddress(contract_address)
            contract_abi = loads(json_abi)['abi']
            return self._w3.eth.contract(abi=contract_abi, address=contract_address,
                                         ContractFactoryClass=ConciseContract)
        except Exception as e:
            raise GethException(str(e), message='Could not get contract instance')

    def claim_token(self, contract_addr, json_abi, user_address, token_id, code=None, gas_price=MAX_GAS_PRICE):
        """ Function for a user to claim a token

        :param contract_addr: The address of the contract
        :param json_abi: The contract's application binary interface as a json string
        :param user_address: The receiving user's address
        :param token_id: The id of the token  !!! Can't be 0 !!!
        :param code: The unique identifier the user is using to claim - default: None
        :param gas_price: The gas price to use - default: MAX_GAS_PRICE (2000000000)
        :return: The address of the transaction
        """
        try:
            # Convert the addresses
            contract_addr = self._w3.toChecksumAddress(contract_addr)
            user_address = self._w3.toChecksumAddress(user_address)

            # Get the contract
            contract_abi = loads(json_abi)['abi']
            contract = self._w3.eth.contract(address=contract_addr, abi=contract_abi)

            # Unlock the issuers account
            self._w3.personal.unlockAccount(self._root_acct, self._root_priv_key, duration=ACCT_UNLOCK_DUR)

            # Get the claim requirements to send
            code = bytes(code, 'utf8') if code else bytes('000000', 'utf8')
            date = int((datetime.now() - datetime(1970, 1, 1)).total_seconds())

            # Send the token specified by token_id to the user
            tx_hash = contract.functions.sendToken(user_address, token_id, code, date).transact(
                {'from': self._root_acct, 'gasPrice': gas_price})

            # Lock the issuers account and return
            self._w3.personal.lockAccount(self._root_acct)
            return hexlify(tx_hash), gas_price
        except Exception as e:
            raise GethException(str(e), message='Could not send token')

    # TODO: add function to get contract instance and get a user's collection
    def get_user_from_token_id(self, contract_addr, json_abi, token_id):
        """ Gets the address of the user who owns the given token_id for the given contract

        :param contract_addr: The address of the contract
        :param json_abi: The ABI for the contract
        :param token_id: The token_id of the token of interest
        :return: An address of the user who owns it or zero bytes
        """
        contract_addr = self._w3.toChecksumAddress(contract_addr)
        try:
            contract_abi = loads(json_abi)['abi']
            contract = self._w3.eth.contract(address=contract_addr, abi=contract_abi,
                                             ContractFactoryClass=ConciseContract)
            return contract.getUserFromTokenID(token_id)
        except Exception as e:
            raise GethException(str(e), message='Could not get an instance of the contract')

    def get_eth_balance(self, user_address):
        """ Returns the balance for the given issuer

        :param user_address: The address of the user's wallet
        :return: Integer representing the user's balance in wei
        """
        try:
            user_address = self._w3.toChecksumAddress(user_address)
            balance = self._w3.eth.getBalance(user_address)
            balance = balance / 1000000000000000000
            return round(balance, 8)
        except Exception as e:
            raise GethException(str(e), message='Could not get eth balance')

    def perform_transfer(self, contract_addr, json_abi, token_id, src_acct=None, dest_acct=None, src_priv_key=None):
        """ Transfers the given token from the src_acct to dest_acct

        :param contract_addr: The address of the contract
        :param json_abi: The ABI for the contract
        :param token_id: The token_id
        :param src_acct: The address of the source account
        :param dest_acct: The address of the destination account
        :param src_priv_key: The private key of the source account
        """
        # Make sure we have the correct arguments
        if not src_acct and not dest_acct:
            raise GethException('', 'Need to provide either the source or destination account')
        if src_acct and not src_priv_key:
            raise GethException('', 'Need to provide the private key of the source account')

        # Set the root account as either the source or destination account
        if not src_acct:
            src_acct = self._root_acct
            src_priv_key = self._root_priv_key
            dest_acct = self._w3.toChecksumAddress(dest_acct)
        elif not dest_acct:
            dest_acct = self._root_acct
            src_acct = self._w3.toChecksumAddress(src_acct)
        else:
            src_acct = self._w3.toChecksumAddress(src_acct)
            dest_acct = self._w3.toChecksumAddress(dest_acct)

        try:
            contract_addr = self._w3.toChecksumAddress(contract_addr)

            contract_abi = loads(json_abi)['abi']
            contract = self._w3.eth.contract(address=contract_addr, abi=contract_abi,
                                             ContractFactoryClass=ConciseContract)
            self._w3.personal.unlockAccount(src_acct, src_priv_key, duration=ACCT_UNLOCK_DUR)
            contract.safeTransferFrom(src_acct, dest_acct, token_id)
            self._w3.personal.lockAccount(src_acct)
        except Exception as e:
            raise GethException(str(e), message='Could not transfer token')

    def send_eth(self, eth_amt, src_acct=None, dest_acct=None, src_priv_key=None, 
                 gas_price=MAX_GAS_PRICE):
        """ Sends the given eth amount to the given dest_addr from the given src_addr

        :param eth_amt: The amount of ethereum to send
        :param src_acct: The address of the source account
        :param dest_acct: The address of the destination account
        :param src_priv_key: The private key of the source account
        :param gas_price: The gasPrice value to use
        """
        if not src_acct and not dest_acct:
            raise GethException('', 'Need to provide at least a source or destination account')
        if src_acct and not src_priv_key:
            raise GethException('', 'Need to provide the private key for the specified source account')

        # Set the root account if needed and correct the addresses
        if not src_acct:
            src_acct = self._root_acct
            src_priv_key = self._root_priv_key
            dest_acct = self._w3.toChecksumAddress(dest_acct)
        elif not dest_acct:
            dest_acct = self._root_acct
            src_acct = self._w3.toChecksumAddress(src_acct)
        else:
            src_acct = self._w3.toChecksumAddress(src_acct)
            dest_acct = self._w3.toChecksumAddress(dest_acct)

        # Perform the transfer
        try:
            transaction = {
                'to': dest_acct,
                'from': src_acct,
                'value': self._w3.toWei(eth_amt, 'ether'),
                'gasPrice': gas_price
            }
            self._w3.personal.unlockAccount(src_acct, src_priv_key, duration=ACCT_UNLOCK_DUR)
            self._w3.eth.sendTransaction(transaction)
            self._w3.personal.lockAccount(src_acct)
        except Exception as e:
            raise GethException(str(e), message='Could not transfer ethereum')

    def kill_contract(self, contract_addr, json_abi, gas_price=MAX_GAS_PRICE):
        """ Kills the given contract

        :param contract_addr: The address of the contract
        :param json_abi: The contract's application binary interface as a json string
        :param gas_price: The gas price to use - default: MAX_GAS_PRICE (2000000000)
        :return: The transaction hash of calling the kill function
        """
        try:
            # Get the contract
            contract_abi = loads(json_abi)['abi']
            contract_addr = self._w3.toChecksumAddress(contract_addr)
            contract = self._w3.eth.contract(address=contract_addr, abi=contract_abi)

            # Unlock the issuers account
            self._w3.personal.unlockAccount(self._root_acct, self._root_priv_key, duration=ACCT_UNLOCK_DUR)

            # Send the token specified by token_id to the user
            tx_hash = contract.functions.kill().transact({'from': self._root_acct, 'gasPrice': gas_price})

            # Lock the issuers account and return
            self._w3.personal.lockAccount(self._root_acct)
            return hexlify(tx_hash)
        except Exception as e:
            raise GethException(str(e), message='Could not kill contract!!!')
