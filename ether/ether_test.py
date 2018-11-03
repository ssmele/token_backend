from binascii import unhexlify
from time import sleep

from ether.geth_keeper import GethKeeper

if __name__ == '__main__':
    gk = GethKeeper()

    create_contract = True
    claim_token = True
    transfer_token = True

    TOKEN_ID = 5
    SRC_ACCT = "0x9db3052c0173adada374173a0286f7855222a713"
    DEST_ACCT = "0x9db3052c0173adada374173a0286f7855222a713"


    if create_contract:
        tx_hash, json_abi = gk.issue_contract('0xff95b24806e3d93afc628c4bb684fd245e9853e9',
                                              issuer_name='tesla', desc='token for tesla', img_url='http://google.com',
                                              num_tokes=5, tradable=False)

        print('tx_hash: {0}'.format(tx_hash))
        print('---------------------------------------------------------------')
        print('json_abi: {0}'.format(json_abi))

        contract_addr = None
        while contract_addr is None:
            print('waiting for contract mine')
            sleep(5)
            _, _, contract_addr = gk.check_contract_mine(tx_hash)

        print('------------------------CONTRACT_CREATED-------------------------')
        print('contract_addr: {0}'.format(contract_addr))

        contract = gk.get_contract_instance(json_abi, contract_addr)
        print('issuer_name: {0}'.format(contract.issuerName()))
        print('contract_name: {0}'.format(contract.name()))
        print('description: {0}'.format(contract.description()))
        print('imageURL: {0}'.format(contract.imageURL()))
        print('totalSupply: {0}'.format(contract.totalSupply()))
        print('remainingTokens: {0}'.format(contract.remainingTokens()))

    # Address and ABI of an already created contract
    else:
        contract_addr = '0x04dC54EC9EBcdf4cc0209604e84191a673cde983'
        json_abi = '{"abi": [{"constant": true, "inputs": [], "name": "num_codes", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "num_locations", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "num_dates", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [{"name": "_user", "type": "address"}], "name": "ownsToken", "outputs": [{"name": "", "type": "bool"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "issuerName", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": false, "inputs": [], "name": "kill", "outputs": [], "payable": false, "stateMutability": "nonpayable", "type": "function"}, {"constant": false, "inputs": [{"name": "_to", "type": "address"}, {"name": "_tokenId", "type": "uint256"}, {"name": "code", "type": "bytes6"}, {"name": "date", "type": "uint256"}], "name": "sendToken", "outputs": [], "payable": false, "stateMutability": "nonpayable", "type": "function"}, {"constant": true, "inputs": [], "name": "description", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [{"name": "_user", "type": "address"}], "name": "getUsersToken", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [{"name": "_token_id", "type": "uint256"}], "name": "getUserFromTokenID", "outputs": [{"name": "", "type": "address"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "imageURL", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [{"name": "index", "type": "uint256"}], "name": "get_code", "outputs": [{"name": "", "type": "bytes6"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [{"name": "index", "type": "uint256"}], "name": "get_date_range", "outputs": [{"name": "", "type": "uint256"}, {"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [{"name": "index", "type": "uint256"}], "name": "get_location", "outputs": [{"name": "", "type": "int256"}, {"name": "", "type": "int256"}, {"name": "", "type": "int256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "remainingTokens", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"inputs": [{"name": "_owner", "type": "address"}, {"name": "_in", "type": "string"}, {"name": "_cn", "type": "string"}, {"name": "_ts", "type": "string"}, {"name": "_cd", "type": "string"}, {"name": "_iu", "type": "string"}, {"name": "_it", "type": "uint256"}, {"name": "_codes", "type": "bytes6[]"}, {"name": "_dates", "type": "uint256[]"}, {"name": "_locs", "type": "int256[]"}], "payable": false, "stateMutability": "nonpayable", "type": "constructor"}]}'

    if claim_token:
        # Claim the token for that user
        tx_hash, gas_price = gk.claim_token(contract_addr, json_abi, SRC_ACCT,
                                            TOKEN_ID, code='123ABC')

        print('tx_hash: {0}, gas_price: {1}'.format(tx_hash, gas_price))

        tx_hash = unhexlify(tx_hash)
        receipt = None
        while not receipt:
            print('waiting for claim mine')
            sleep(5)
            receipt = gk._w3.eth.getTransactionReceipt(tx_hash)

        print('-----------RECEIPT-----------')
        print('receipt: {0}'.format(receipt))
        print('-----------RECEIPT END-----------')

        addr = gk.get_user_from_token_id(contract_addr, json_abi, TOKEN_ID)
        print('\nUser Address For Token ID: {addr}'.format(addr=addr))
        print('Type of addr: {t}'.format(t=type(addr)))

    if transfer_token:
        tx_hash, gas_price = gk.perform_transfer(contract_addr, json_abi, TOKEN_ID, src_acct=SRC_ACCT,
                                                 dest_acct=DEST_ACCT)

        print('tx_hash: {0}, gas_price: {1}'.format(tx_hash, gas_price))

        tx_hash = unhexlify(tx_hash)
        receipt = None
        while not receipt:
            print('waiting for transfer mine')
            sleep(5)
            receipt = gk._w3.eth.getTransactionReceipt(tx_hash)

        print('---------RECEIPT---------')
        print('receipt: {0}'.format(receipt))
        print('---------RECEIPT END----------')

        addr = gk.get_user_from_token_id(contract_addr, json_abi, TOKEN_ID)
        print('\nUser Address For Token ID after Trade: {addr}'.format(addr=addr))
        print('Type of addr: {t}'.format(t=type(addr)))

    # accts = ["0xff95b24806e3d93afc628c4bb684fd245e9853e9", "0x8ed9826772d8dca0ddf9edf1799c8b6bc0a5e799", "0x5b29a628d650c9928a52d240b3e1aa5ae7e7f1e5", "0xa6040aa06cde8aaa293aafee1cd0baf2500789fe", "0x981d604d07e4f4e1a092fcb453d9bd881f9a465e", "0xc3031fc61ae717562d06df9d817f4a555345adf5", "0x74915a09a3ea76ecfc41471791ec1f676e1d1d73", "0x0ea1eadb5fd5c4aff6492140229b412371c27f58", "0xdd8e2942cb9ed73edd10ad4c46a8ad41fd9e273f", "0xabd018220defea8ac5a1008b12d40fdb2dec7a78", "0xe941e23219b41ce67f659d80611ab6337b15d20f", "0x0aa665571621c92a588519b0471c11f8577e2c33", "0xc52adce2223558bebba5959e0a597f9f3112cd05", "0xbdd61fdab9f841013e8be1be2bff10e8d00c4643", "0xf4d8350d912ccd6310439444163f0987b0dd51cd", "0xf1ed0c7d178e18f59f1bb86c20579e6cc3e592f6", "0xc532b699bfdffda7be32f00fe097f5de95d62510", "0x296795c9797b67b2c24d0bbaa18300ae241f217f", "0xca1d9b3bf30ffc9add30b963b53b3c2661a5b2be", "0x7c14fddf667ffac720d1edbdb9718f0cb7579e0b", "0x450d2065450e9dd48a8b103d29e035d2d86e887f", "0xc5e0460c8eca0b931e94c7a328c9d9af6a1ba6d6", "0x84d8bef0a65e54ba4615dd17c137fe308ff6616b", "0x38f16b5b1ede9ae6ed21453c6c24ff44d151879e", "0xd2ae7a28b140c74ac344d6794e955de42142ff49", "0x76444f4baff8560128a85497937aff8d88c05b6c", "0xe756063d758969bcd0cf856487b0c2922b79c8e4", "0x4ac88b7edc5797c016030d74a16c0d6e44ed4a7c", "0x648caf3cdad5a009e6361006ca463d1b1298acb7", "0x064199cdeaf85c9e227a065242bf0e10630876f1", "0x863f96933389b014c71fe43f8cd2e9819a9136fd", "0x464e3eb48b0349c9bac47804bf64ba85d05910d4", "0x4b5b3dc4790b6ddc92dc7fdc95028ffa89e85b9e", "0x7f16dc14fd1bf0dcb6caf23393adb3a5d2635a07", "0x9127aaec455df28bad852f0f9098c0ea157a9376", "0x006ef15e8a8942e28b314ab2090bdc0e4e3c0b97", "0xb6704ec577c9770ab85ea34e87f426d24bb716e7", "0x361615c7a05e46de7398d4d078364c6e95dcef58", "0x9f3600c7a20e417ed0767fee373dfece4862d97a", "0x7cc29cd477d44acc84e32602ce68125f8dd95836", "0xd2f47a11b36217967f67860ee42a15b1f904ba73", "0x9aa904f5e47ba0c9fde8d4c9966c377f5ed33960", "0x321ba886ab8e0d0fbd303fd7530a11aed9062237", "0x1cb8e29adc20ad21e2816c428fe2fdd16bb84650", "0xc274e39e9197ce15e4823d96871bb985ff03a649", "0x92f65cb7aa43f6c79e51cade519c6dabacbb7e84", "0x081a41bd012b29c1723b1f58e2991c51780acb5b", "0xa98951bca663936e6275c41683078237302f1f02", "0x90f03442b334cd140820fee7a202d4e477c2e1bb", "0xdc5900ad615c60a7db2383e9d197b2f5df9fa50b", "0xedf32f02f4d720e1c01da04ebbeee7a830a736ef", "0x713d3c61dad74d9ae627cc8c03981342783ce0c1", "0x8da0a4907e42b35ee7dabcc9f12118f9663320e6", "0x52905368ac61d76a0178b52d87676409ee570e67", "0x7a98ddf0e532a14614185c47821d2ee7da1a8a96", "0xa79a9f01ef78f36b9399e9c7b6aabbe6b50e8848", "0x27792ab3227852b28d064acbc53cc356167c91b0", "0x630b04d166617d5e6137ade2d1b3cd997f8b6c59", "0x38cc9cf76b9217200da58d2653ea197a65c9a312", "0xbaf85145688ba8de2a5a209c3a548e1dcb9ef946", "0x982bbcde0c6ad5b6866e874b02b9555b0ff5b9a0", "0xf2287e5a275430361d21ee9036de9e21239fb44a", "0x451a8ef2ed1bf854314043efebc5338dbafdea68", "0xba51bbde7dc139739ce1d7db989eb62d857369ce", "0x9a8a1fc0091dd0418f4de140250e6431a348cc41", "0xc2ed4cf6ff12279e2ec30c5a96fa7a923271f981", "0x81472f4750864c3b9d612a2269fcd2c0d4b591be", "0x9657077fd00f187dc9898f39d35e868bd2f815ca", "0x354d6124ffb3a8eb770a9f4cef2ec173dffd38da", "0x738af39778aa4674309c84296b2c213f6a7f39d4", "0x4f7c644d04738a5ff0ac21c53b5984ad73fd3af7", "0x9db3052c0173adada374173a0286f7855222a713", "0xee84fba2094574e741a4b716f64d424c3c6eee43", "0xfe84822a4d358a194a839a4dadfd63e47c54bedb", "0x9986a81fef3da9ccb028c747c554a879f4f76a4e", "0xae7f14ec021a4ea7990b2a2a770b48be0a2a6876", "0x43c98e649069b9d5c32c8b11fdb74e63d91884a1", "0xf19563a0d1c510ef0cd1a04669efad2bcd72da40", "0x7a358f0d2bf13b5ede968b178b3e9a97ea7df375", "0x6e3705b215ac91d31f5c95c04b07003ee8c1dca9", "0x02f639833a533f90f64a449c61bdc7313c5e0d5a", "0xf5e4231d8fddc59af3a7734d00de36c9c166c55a", "0x524eac68818160fa05fc13694001e4da8ffcbb0e", "0xa1fe6232ca9602cc2ca7751b9c18eb379355cde0", "0x291d74b393adc9dcff850877ef8b2a97bb8b311c", "0x35af8675e29fccc1f25a9635bcb199851717527d", "0x70c3c51a778968bd4b0e65c3ceca3af7ff9f8d79", "0x38fd11ed463e7647593b57486af42db03ac9a01c", "0xa88045f36c0972a8631d8cb9c1940122a2de25a1", "0x41079ba2e9a7334972bd2c34cce873214a733840", "0xe5c2edd7a633c035400f8a6b3bf7664f162c3f8b", "0xcdf636a80c4b19db8105f39f2f7f7c9e11e09eca", "0xd6648e58cf969076f15b6b9c9a485a4307124929", "0x433e243e3c236b55a8524ce15a3aa51e95a051ed", "0xee53de91b8ddaddb6a5fcda777c98d5d7af4e251", "0x9b1f4d847cf0d3a66dd7a1fd99dec9c7fb41ef32", "0xfcd9a4d1d0f69c80321579b0d3940e8118842287", "0x13317c0b3143c32908d55a3bba1cd4438a4a98bf", "0xcbe44c5ae3e3ee51e4b325b854ee749ec834aa75", "0xc781677430a70e978ec8357b82243c2458ec40ed", "0xc125ed0647003cb1bf728b047daea38468933fc7", "0x6ab9777f46ccbc8269d4a78ca7b5d6da20fb2e17"]
    # for acct in accts:
    #     res = gk.get_users_token_id(contract_addr, json_abi, acct)
    #     if res != -1:
    #         print('{acct} owns {res}'.format(acct=acct, res=res))

    # print('Checking if user owns token')
    # res = gk.get_users_token_id(contract_addr, json_abi, '0xEe53de91b8dDADdB6a5FcdA777C98d5d7af4E251')
    # print('GOT RESULT: {}'.format(res))

    #
    # contract = gk.get_contract_instance(json_abi, contract_addr)
    # print('issuer_name: {0}'.format(contract.issuerName()))
    # print('contract_name: {0}'.format(contract.name()))
    # print('description: {0}'.format(contract.description()))
    # print('imageURL: {0}'.format(contract.imageURL()))
    # print('totalSupply: {0}'.format(contract.totalSupply()))
    # print('remainingTokens: {0}'.format(contract.remainingTokens()))

    # print('receipt: {0}'.format(gk.check_claim_mine('27bedf44c5a934a030a3f0d087555355379c250d22bdd6c254ef0a0ddbe7fb79')))
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
