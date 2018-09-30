from binascii import hexlify, unhexlify
from time import sleep

from ether.geth_keeper import GethException, GethKeeper

if __name__ == '__main__':
    gk = GethKeeper()

    # tx_hash, json_abi = gk.issue_contract('0xff95b24806e3d93afc628c4bb684fd245e9853e9',
    #                                       issuer_name='tesla', desc='token for tesla', img_url='http://google.com',
    #                                       num_tokes=100)
    #
    # print('tx_hash: {0}'.format(tx_hash))
    # print('---------------------------------------------------------------')
    # print('json_abi: {0}'.format(json_abi))
    #
    # contract_addr = None
    # while contract_addr is None:
    #     print('waiting for contract mine')
    #     sleep(5)
    #     _, _, contract_addr = gk.check_contract_mine(tx_hash)
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

    # Address and ABI of an already created contract
    contract_addr = '0xe9d629979815D2946dE1FBD3E6DA5f29A6D0B1D6'
    json_abi = '{"abi": [{"constant": true, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [{"name": "_user", "type": "address"}], "name": "ownsToken", "outputs": [{"name": "", "type": "bool"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "issuerName", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": false, "inputs": [{"name": "_to", "type": "address"}, {"name": "_tokenId", "type": "uint256"}], "name": "sendToken", "outputs": [], "payable": false, "stateMutability": "nonpayable", "type": "function"}, {"constant": false, "inputs": [], "name": "kill", "outputs": [], "payable": false, "stateMutability": "nonpayable", "type": "function"}, {"constant": true, "inputs": [], "name": "description", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [{"name": "_user", "type": "address"}], "name": "getUsersToken", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "imageURL", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "remainingTokens", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"inputs": [{"name": "_owner", "type": "address"}, {"name": "_in", "type": "string"}, {"name": "_cn", "type": "string"}, {"name": "_ts", "type": "string"}, {"name": "_cd", "type": "string"}, {"name": "_iu", "type": "string"}, {"name": "_it", "type": "uint256"}], "payable": false, "stateMutability": "nonpayable", "type": "constructor"}]}'

    # Claim the token for that user
    tx_hash = gk.claim_token(contract_addr, json_abi, "0x9986a81fef3da9ccb028c747c554a879f4f76a4e", 120304)

    print('tx_hash: {0}'.format(tx_hash))

    tx_hash = unhexlify(tx_hash)
    receipt = None
    while not receipt:
        print('waiting for claim mine')
        sleep(5)
        receipt = gk._w3.eth.getTransactionReceipt(tx_hash)

    print('-----------RECEIPT-----------')
    print('receipt: {0}'.format(receipt))
    print('-----------RECEIPT END-----------')
    #
    # contract = gk.get_contract_instance(json_abi, contract_addr)
    # print('issuer_name: {0}'.format(contract.issuerName()))
    # print('contract_name: {0}'.format(contract.name()))
    # print('description: {0}'.format(contract.description()))
    # print('imageURL: {0}'.format(contract.imageURL()))
    # print('totalSupply: {0}'.format(contract.totalSupply()))
    # print('remainingTokens: {0}'.format(contract.remainingTokens()))

    #print('receipt: {0}'.format(gk.check_claim_mine('27bedf44c5a934a030a3f0d087555355379c250d22bdd6c254ef0a0ddbe7fb79')))
    #
    # print(gk.issue_contract('0xff95b24806e3d93afc628c4bb684fd245e9853e9', 'test', 'c_name', num_tokes=4))

    # TODO: Below is the result of a token claim mine. From here we can extract gasUsed
    # AttributeDict({'blockHash': HexBytes('0xa818276648751254b064c065d1bd6eb258c546e4da8cc10e2ff6d185026b3b96'),
    #                'blockNumber': 3080493, 'contractAddress': None, 'cumulativeGasUsed': 3450099,
    #                'from': '0xff95b24806e3d93afc628c4bb684fd245e9853e9', 'gasUsed': 90776, 'logs': [],
    #                'logsBloom': HexBytes(
    #                    '0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'),
    #                'status': 1, 'to': '0xe9d629979815d2946de1fbd3e6da5f29a6d0b1d6',
    #                'transactionHash': HexBytes('0x9b9cdcaf716945275492a48fdf3edf7738fbb7a9dc09ce972ea0e70e8ce54e76'),
    #                'transactionIndex': 19})
