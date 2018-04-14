from binascii import hexlify
from time import sleep

from ether.geth_keeper import GethException, GethKeeper

if __name__ == '__main__':
    gk = GethKeeper()
    tx_hash, json_abi = gk.issue_contract('0xff95b24806e3d93afc628c4bb684fd245e9853e9', 'jhensley1234',
                                          issuer_name='tesla', desc='token for tesla', img_url='http://google.com',
                                          num_tokes=100)

    print('tx_hash: {0}'.format(tx_hash))
    print('---------------------------------------------------------------')
    print('json_abi: {0}'.format(json_abi))

    contract_addr = None
    while contract_addr is None:
        sleep(10)
        contract_addr = gk.check_contract_mine(tx_hash)

    print('------------------------CONTRACT_CREATED-------------------------')
    print('contract_addr: {0}'.format(contract_addr))

    contract = gk.get_contract_instance(json_abi, contract_addr)
    print('issuer_name: {0}'.format(contract.issuerName()))
    print('contract_name: {0}'.format(contract.name()))
    print('description: {0}'.format(contract.description()))
    print('imageURL: {0}'.format(contract.imageURL()))
    print('totalSupply: {0}'.format(contract.totalSupply()))
    print('remainingTokens: {0}'.format(contract.remainingTokens()))
