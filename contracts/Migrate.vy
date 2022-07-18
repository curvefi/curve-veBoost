# @version 0.3.3


interface BoostV1:
    def tokenByIndex(_idx: uint256) -> uint256: view
    def totalSupply() -> uint256: view
    def token_expiry(_token_id: uint256) -> uint256: view

interface BoostV2:
    def migrate(_token_id: uint256): nonpayable


@external
def __init__(_boost_v1: address, _boost_v2: address):
    total: uint256 = BoostV1(_boost_v1).totalSupply()
    for i in range(256):
        if i == total:
            break
        token_id: uint256 = BoostV1(_boost_v1).tokenByIndex(i)
        if BoostV1(_boost_v1).token_expiry(token_id) <= block.timestamp:
            continue
        BoostV2(_boost_v2).migrate(token_id)
    selfdestruct(msg.sender)
