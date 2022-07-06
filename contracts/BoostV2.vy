# @version 0.3.3
"""
@title Boost Delegation V2
@author CurveFi
"""


interface VotingEscrow:
    def totalSupply(_ts: uint256) -> uint256: view
    def totalSupplyAt(_block: uint256) -> uint256: view


NAME: constant(String[32]) = "Vote-Escrowed Boost"
SYMBOL: constant(String[8]) = "veBoost"


VE: immutable(address)


@external
def __init__(_ve: address):
    VE = _ve


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
