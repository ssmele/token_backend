from binascii import hexlify, unhexlify
from time import sleep

from ether.geth_keeper import GethException, GethKeeper

if __name__ == '__main__':
    gk = GethKeeper()
    # tx_hash, json_abi = gk.issue_contract('0xff95b24806e3d93afc628c4bb684fd245e9853e9', 'jhensley1234',
    #                                       issuer_name='tesla', desc='token for tesla', img_url='http://google.com',
    #                                       num_tokes=100)
    #
    # print('tx_hash: {0}'.format(tx_hash))
    # print('---------------------------------------------------------------')
    # print('json_abi: {0}'.format(json_abi))
    #
    # contract_addr = None
    # while contract_addr is None:
    #     sleep(10)
    #     contract_addr = gk.check_contract_mine(tx_hash)
    #
    # print('------------------------CONTRACT_CREATED-------------------------')
    # print('contract_addr: {0}'.format(contract_addr))
    #
    # contract = gk.get_contract_instance(json_abi, contract_addr)
    # print('issuer_name: {0}'.format(contract.issuerName()))
    # print('contract_name: {0}'.format(contract.name()))
    # print('description: {0}'.format(contract.description()))
    # print('imageURL: {0}'.format(contract.imageURL()))
    # print('totalSupply: {0}'.format(contract.totalSupply()))
    # print('remainingTokens: {0}'.format(contract.remainingTokens()))

    # Claim Token
    # contract_addr = '0x40bcCF81D2651F62B51ba61C4Bf5b5c82D10d482'
    # json_abi = '{"abi": [{"constant": true, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [{"name": "_user", "type": "address"}], "name": "ownsToken", "outputs": [{"name": "", "type": "bool"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "issuerName", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": false, "inputs": [{"name": "_to", "type": "address"}, {"name": "_tokenId", "type": "uint256"}], "name": "sendToken", "outputs": [], "payable": false, "stateMutability": "nonpayable", "type": "function"}, {"constant": false, "inputs": [], "name": "kill", "outputs": [], "payable": false, "stateMutability": "nonpayable", "type": "function"}, {"constant": true, "inputs": [], "name": "description", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [{"name": "_user", "type": "address"}], "name": "getUsersToken", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "imageURL", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "remainingTokens", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"inputs": [{"name": "_in", "type": "string"}, {"name": "_cn", "type": "string"}, {"name": "_ts", "type": "string"}, {"name": "_cd", "type": "string"}, {"name": "_iu", "type": "string"}, {"name": "_it", "type": "uint256"}], "payable": false, "stateMutability": "nonpayable", "type": "constructor"}]}'
    # tx_hash = gk.claim_token('0xff95b24806e3d93afc628c4bb684fd245e9853e9', 'jhensley1234',
    #                          contract_addr, json_abi, '0xcc0c1a4651e91101dc18348f5ef50fed73ba7c71', 1)
    #
    # print('tx_hash: {0}'.format(tx_hash))
    #
    # receipt = None
    # while receipt is None:
    #     sleep(10)
    #     receipt = gk.check_claim_mine(tx_hash)
    #
    # print('-----------RECEIPT-----------')
    # print('receipt: {0}'.format(receipt))
    # print('-----------RECEIPT END-----------')
    #
    # contract = gk.get_contract_instance(json_abi, contract_addr)
    # print('issuer_name: {0}'.format(contract.issuerName()))
    # print('contract_name: {0}'.format(contract.name()))
    # print('description: {0}'.format(contract.description()))
    # print('imageURL: {0}'.format(contract.imageURL()))
    # print('totalSupply: {0}'.format(contract.totalSupply()))
    # print('remainingTokens: {0}'.format(contract.remainingTokens()))

    #print('receipt: {0}'.format(gk.check_claim_mine('27bedf44c5a934a030a3f0d087555355379c250d22bdd6c254ef0a0ddbe7fb79')))

    print(gk.create_account())
