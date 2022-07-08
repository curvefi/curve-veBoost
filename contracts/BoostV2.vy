# @version 0.3.3
"""
@title Boost Delegation V2
@author CurveFi
"""


event Approval:
    _owner: indexed(address)
    _spender: indexed(address)
    _value: uint256

event Transfer:
    _from: indexed(address)
    _to: indexed(address)
    _value: uint256


interface VotingEscrow:
    def balanceOf(_user: address) -> uint256: view
    def totalSupply() -> uint256: view
    def locked__end(_user: address) -> uint256: view


struct Point:
    bias: int256
    slope: int256
    ts: uint256


NAME: constant(String[32]) = "Vote-Escrowed Boost"
SYMBOL: constant(String[8]) = "veBoost"
VERSION: constant(String[8]) = "v2.0.0"

EIP712_TYPEHASH: constant(bytes32) = keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract,bytes32 salt)")
PERMIT_TYPEHASH: constant(bytes32) = keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)")

WEEK: constant(uint256) = 86400 * 7


DOMAIN_SEPARATOR: immutable(bytes32)
VE: immutable(address)


allowance: public(HashMap[address, HashMap[address, uint256]])
nonces: public(HashMap[address, uint256])

delegated_epoch: public(HashMap[address, uint256])
delegated_point_history: public(HashMap[address, Point[100000000000000000000000000000000]])
delegated_slope_changes: public(HashMap[address, HashMap[uint256, int256]])

received_epoch: public(HashMap[address, uint256])
received_point_history: public(HashMap[address, Point[100000000000000000000000000000000]])
received_slope_changes: public(HashMap[address, HashMap[uint256, int256]])


@external
def __init__(_ve: address):
    DOMAIN_SEPARATOR = keccak256(_abi_encode(EIP712_TYPEHASH, keccak256(NAME), keccak256(VERSION), chain.id, self, block.prevhash))
    VE = _ve


@view
@internal
def _read_bias(_user: address, _delegated: bool) -> uint256:
    epoch: uint256 = 0
    point: Point = Point({bias: 0, slope: 0, ts: block.timestamp})

    if _delegated:
        epoch = self.delegated_epoch[_user]
        if epoch != 0:
            point = self.delegated_point_history[_user][epoch]
    else:
        epoch = self.received_epoch[_user]
        if epoch != 0:
            point = self.received_point_history[_user][epoch]

    if point.ts == block.timestamp:
        return convert(point.bias, uint256)

    ts: uint256 = (point.ts / WEEK) * WEEK
    for _ in range(255):
        ts += WEEK

        dslope: int256 = 0
        if block.timestamp < ts:
            ts = block.timestamp
        else:
            if _delegated:
                dslope = self.delegated_slope_changes[_user][ts]
            else:
                dslope = self.received_slope_changes[_user][ts]

        point.bias -= point.slope * convert(ts - point.ts, int256)
        point.slope -= dslope
        point.ts = ts

        if ts == block.timestamp:
            break

    return convert(point.bias, uint256)


@external
def boost(_to: address, _amount: uint256, _endtime: uint256, _from: address = msg.sender):
    assert _to not in [_from, ZERO_ADDRESS]
    assert _amount != 0
    assert _endtime > block.timestamp
    assert _endtime % WEEK == 0

    assert _amount <= VotingEscrow(VE).balanceOf(_from)
    assert _endtime <= VotingEscrow(VE).locked__end(_from)

    # reduce approval if necessary
    if _from != msg.sender:
        allowance: uint256 = self.allowance[_from][msg.sender]
        if allowance != MAX_UINT256:
            self.allowance[_from][msg.sender] = allowance - _amount
            log Approval(_from, msg.sender, allowance - _amount)


@external
def approve(_spender: address, _value: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _value

    log Approval(msg.sender, _spender, _value)
    return True


@external
def permit(_owner: address, _spender: address, _value: uint256, _deadline: uint256, _v: uint8, _r: bytes32, _s: bytes32) -> bool:
    assert _owner != ZERO_ADDRESS
    assert block.timestamp <= _deadline

    nonce: uint256 = self.nonces[_owner]
    digest: bytes32 = keccak256(
        concat(
            b"\x19\x01",
            DOMAIN_SEPARATOR,
            keccak256(_abi_encode(PERMIT_TYPEHASH, _owner, _spender, _value, nonce, _deadline))
        )
    )

    assert ecrecover(digest, convert(_v, uint256), convert(_r, uint256), convert(_s, uint256)) == _owner

    self.allowance[_owner][_spender] = _value
    self.nonces[_owner] = nonce + 1

    log Approval(_owner, _spender, _value)
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
def balanceOf(_user: address) -> uint256:
    return VotingEscrow(VE).balanceOf(_user) - self._read_bias(_user, True) + self._read_bias(_user, False)


@view
@external
def totalSupply() -> uint256:
    return VotingEscrow(VE).totalSupply()


@view
@external
def delegated_balance(_user: address) -> uint256:
    return self._read_bias(_user, True)


@view
@external
def received_balance(_user: address) -> uint256:
    return self._read_bias(_user, False)


@view
@external
def delegable_balance(_user: address) -> uint256:
    return VotingEscrow(VE).balanceOf(_user) - self._read_bias(_user, True)


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


@pure
@external
def DOMAIN_SEPARATOR() -> bytes32:
    return DOMAIN_SEPARATOR
