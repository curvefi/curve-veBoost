# @version 0.3.3
"""
@title Boost Delegation V2
@author CurveFi
"""


event Approval:
    _owner: indexed(address)
    _spender: indexed(address)
    _value: uint256


interface VotingEscrow:
    def totalSupply(_ts: uint256) -> uint256: view
    def totalSupplyAt(_block: uint256) -> uint256: view


NAME: constant(String[32]) = "Vote-Escrowed Boost"
SYMBOL: constant(String[8]) = "veBoost"


VE: immutable(address)


allowance: public(HashMap[address, HashMap[address, uint256]])


@external
def __init__(_ve: address):
    VE = _ve


@external
def approve(_spender: address, _value: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _value

    log Approval(msg.sender, _spender, _value)
    return True


@external
def increaseAllowance(_spender: address, _added_value: uint256) -> bool:
    allowance: uint256 = self.allowance[msg.sender][_spender] + _added_value
    self.allowance[msg.sender][_spender] = allowance

    log Approval(msg.sender, _spender, allowance)
    return True


@external
def decreaseAllowance(_spender: address, _subtracted_value: uint256) -> bool:
    allowance: uint256 = self.allowance[msg.sender][_spender] - _subtracted_value
    self.allowance[msg.sender][_spender] = allowance

    log Approval(msg.sender, _spender, allowance)
    return True


@view
@external
def totalSupply(_ts: uint256 = block.timestamp) -> uint256:
    return VotingEscrow(VE).totalSupply(_ts)


@view
@external
def totalSupplyAt(_block: uint256) -> uint256:
    return VotingEscrow(VE).totalSupplyAt(_block)


@pure
@external
def name() -> String[32]:
    return NAME


@pure
@external
def symbol() -> String[8]:
    return SYMBOL


@pure
@external
def decimals() -> uint8:
    return 18
