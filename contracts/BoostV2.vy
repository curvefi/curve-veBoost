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

delegated: public(HashMap[address, Point])
delegated_slope_changes: public(HashMap[address, HashMap[uint256, int256]])

received: public(HashMap[address, Point])
received_slope_changes: public(HashMap[address, HashMap[uint256, int256]])


@external
def __init__(_ve: address):
    DOMAIN_SEPARATOR = keccak256(_abi_encode(EIP712_TYPEHASH, keccak256(NAME), keccak256(VERSION), chain.id, self, block.prevhash))
    VE = _ve


@view
@internal
def _balance_of(_user: address) -> uint256:
    amount: uint256 = VotingEscrow(VE).balanceOf(_user)
    amount -= convert(self._checkpoint_read(_user, True).bias, uint256)
    amount += convert(self._checkpoint_read(_user, False).bias, uint256)
    return amount


@view
@internal
def _checkpoint_read(_user: address, _delegated: bool) -> Point:
    point: Point = empty(Point)

    if _delegated:
        point = self.delegated[_user]
    else:
        point = self.received[_user]

    if point.ts == 0:
        point.ts = block.timestamp

    if point.ts == block.timestamp:
        return point

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

    return point


@external
def boost(_to: address, _amount: uint256, _endtime: uint256, _from: address = msg.sender):
    assert _to not in [_from, ZERO_ADDRESS]
    assert _amount != 0
    assert _endtime > block.timestamp
    assert _endtime % WEEK == 0
    assert _endtime <= VotingEscrow(VE).locked__end(_from)

    # reduce approval if necessary
    if _from != msg.sender:
        allowance: uint256 = self.allowance[_from][msg.sender]
        if allowance != MAX_UINT256:
            self.allowance[_from][msg.sender] = allowance - _amount
            log Approval(_from, msg.sender, allowance - _amount)

    # checkpoint delegated point
    point: Point = self._checkpoint_read(_from, True)
    assert _amount <= VotingEscrow(VE).balanceOf(_from) - convert(point.bias, uint256)

    # calculate slope and bias being added
    slope: int256 = convert(_amount / (_endtime - block.timestamp), int256)
    bias: int256 = slope * convert(_endtime, int256)

    # update delegated point
    point.bias += bias
    point.slope += slope

    # store updated values
    self.delegated[_from] = point
    self.delegated_slope_changes[_from][_endtime] += slope

    # update received amount
    point = self._checkpoint_read(_to, False)
    point.bias += bias
    point.slope += slope

    # store updated values
    self.received[_to] = point
    self.received_slope_changes[_to][_endtime] += slope

    log Transfer(_from, _to, _amount)

    # also checkpoint received and delegated
    self.received[_from] = self._checkpoint_read(_from, False)
    self.delegated[_to] = self._checkpoint_read(_to, True)


@external
def checkpoint_user(_user: address):
    self.delegated[_user] = self._checkpoint_read(_user, True)
    self.received[_user] = self._checkpoint_read(_user, False)


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
    return self._balance_of(_user)


@view
@external
def adjusted_balance_of(_user: address) -> uint256:
    return self._balance_of(_user)


@view
@external
def totalSupply() -> uint256:
    return VotingEscrow(VE).totalSupply()


@view
@external
def delegated_balance(_user: address) -> uint256:
    return convert(self._checkpoint_read(_user, True).bias, uint256)


@view
@external
def received_balance(_user: address) -> uint256:
    return convert(self._checkpoint_read(_user, False).bias, uint256)


@view
@external
def delegable_balance(_user: address) -> uint256:
    return VotingEscrow(VE).balanceOf(_user) - convert(self._checkpoint_read(_user, True).bias, uint256)


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
