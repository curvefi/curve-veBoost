# @version 0.2.15
"""
@title Voting Escrow Delegation
@author Curve Finance
@license MIT
@dev Provides test functions only available in test mode (`brownie test`)
"""


interface ERC721Receiver:
    def onERC721Received(
        _operator: address, _from: address, _token_id: uint256, _data: Bytes[4096]
    ) -> bytes32:
        nonpayable

interface VotingEscrow:
    def balanceOf(_account: address) -> uint256: view
    def locked__end(_addr: address) -> uint256: view


event Approval:
    _owner: indexed(address)
    _approved: indexed(address)
    _token_id: indexed(uint256)

event ApprovalForAll:
    _owner: indexed(address)
    _operator: indexed(address)
    _approved: bool

event Transfer:
    _from: indexed(address)
    _to: indexed(address)
    _token_id: indexed(uint256)

event BurnBoost:
    _delegator: indexed(address)
    _receiver: indexed(address)
    _token_id: indexed(uint256)

event DelegateBoost:
    _delegator: indexed(address)
    _receiver: indexed(address)
    _token_id: indexed(uint256)
    _amount: uint256
    _cancel_time: uint256
    _expire_time: uint256

event ExtendBoost:
    _delegator: indexed(address)
    _receiver: indexed(address)
    _token_id: indexed(uint256)
    _amount: uint256
    _expire_time: uint256
    _cancel_time: uint256

event TransferBoost:
    _from: indexed(address)
    _to: indexed(address)
    _token_id: indexed(uint256)
    _amount: uint256
    _expire_time: uint256


struct Boost:
    # [bias uint128][slope int128]
    delegated: uint256
    received: uint256

struct Token:
    # [bias uint128][slope int128]
    data: uint256
    cancel_time: uint256


MAX_PCT: constant(uint256) = 10_000
MIN_DELEGATION_TIME: constant(uint256) = 86400
#@ if mode == "test":
VOTING_ESCROW: constant(address) = 0x0000000000000000000000000000000000000000
#@ else:
VOTING_ESCROW: constant(address) = 0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2
#@ endif


balanceOf: public(HashMap[address, uint256])
getApproved: public(HashMap[uint256, address])
isApprovedForAll: public(HashMap[address, HashMap[address, bool]])
ownerOf: public(HashMap[uint256, address])

name: public(String[32])
symbol: public(String[32])

boost: HashMap[address, Boost]
boost_token: HashMap[uint256, Token]

admin: public(address)  # Can and will be a smart contract
future_admin: public(address)
is_killed: public(bool)


@external
def __init__(_name: String[32], _symbol: String[32]):
    self.name = _name
    self.symbol = _symbol


@internal
def _approve(_owner: address, _approved: address, _token_id: uint256):
    self.getApproved[_token_id] = _approved
    log Approval(_owner, _approved, _token_id)


@view
@internal
def _is_approved_or_owner(_spender: address, _token_id: uint256) -> bool:
    owner: address = self.ownerOf[_token_id]
    return (
        _spender == owner
        or _spender == self.getApproved[_token_id]
        or self.isApprovedForAll[owner][_spender]
    )


@internal
def _burn(_token_id: uint256):
    owner: address = self.ownerOf[_token_id]

    self._approve(owner, ZERO_ADDRESS, _token_id)

    self.balanceOf[owner] -= 1
    self.ownerOf[_token_id] = ZERO_ADDRESS

    log Transfer(owner, ZERO_ADDRESS, _token_id)


@internal
def _mint(_to: address, _token_id: uint256):
    assert _to != ZERO_ADDRESS  # dev: minting to ZERO_ADDRESS disallowed
    assert self.ownerOf[_token_id] == ZERO_ADDRESS  # dev: token exists

    self.balanceOf[_to] += 1
    self.ownerOf[_token_id] = _to

    log Transfer(ZERO_ADDRESS, _to, _token_id)


@internal
def _mint_boost(_token_id: uint256, _delegator: address, _receiver: address, _bias: int256, _slope: int256, _cancel_time: uint256):
    data: uint256 = shift(convert(_bias, uint256), 128) + convert(abs(_slope), uint256)
    self.boost[_delegator].delegated += data
    self.boost[_receiver].received += data
    self.boost_token[_token_id] = Token({data: data, cancel_time: _cancel_time})


@internal
def _burn_boost(_token_id: uint256, _delegator: address, _receiver: address, _bias: int256, _slope: int256):
    data: uint256 = shift(convert(_bias, uint256), 128) + convert(abs(_slope), uint256)
    self.boost[_delegator].delegated -= data
    self.boost[_receiver].received -= data
    self.boost_token[_token_id] = empty(Token)


@internal
def _transfer_boost(_from: address, _to: address, _bias: int256, _slope: int256):
    data: uint256 = shift(convert(_bias, uint256), 128) + convert(abs(_slope), uint256)
    self.boost[_from].received -= data
    self.boost[_to].received += data


@pure
@internal
def _deconstruct_bias_slope(_data: uint256) -> (int256, int256):
    return convert(shift(_data, -128), int256), -convert(_data % 2 ** 128, int256)


@internal
def _transfer(_from: address, _to: address, _token_id: uint256):
    assert self.ownerOf[_token_id] == _from  # dev: _from is not owner
    assert _to != ZERO_ADDRESS  # dev: transfers to ZERO_ADDRESS are disallowed

    # clear previous token approval
    self._approve(_from, ZERO_ADDRESS, _token_id)

    self.balanceOf[_from] -= 1
    self.balanceOf[_to] += 1
    self.ownerOf[_token_id] = _to

    tbias: int256 = 0
    tslope: int256 = 0
    tbias, tslope = self._deconstruct_bias_slope(self.boost_token[_token_id].data)

    tvalue: int256 = tslope * convert(block.timestamp, int256) + tbias

    # if the boost value is negative, reset the slope and bias
    if tvalue > 0:
        self._transfer_boost(_from, _to, tbias, tslope)
        # y = mx + b -> y - b = mx -> (y - b)/m = x -> -b / m = x (x-intercept)
        expiry: uint256 = convert(-tbias / tslope, uint256)
        log TransferBoost(_from, _to, _token_id, convert(tvalue, uint256), expiry)
    else:
        self._burn_boost(_token_id, convert(shift(_token_id, -96), address), _from, tbias, tslope)

    log Transfer(_from, _to, _token_id)


@external
def approve(_approved: address, _token_id: uint256):
    """
    @notice Change or reaffirm the approved address for an NFT.
    @dev The zero address indicates there is no approved address.
        Throws unless `msg.sender` is the current NFT owner, or an authorized
        operator of the current owner.
    @param _approved The new approved NFT controller.
    @param _token_id The NFT to approve.
    """
    owner: address = self.ownerOf[_token_id]
    assert (
        msg.sender == owner or self.isApprovedForAll[owner][msg.sender]
    )  # dev: must be owner or operator
    self._approve(owner, _approved, _token_id)


@external
def safeTransferFrom(_from: address, _to: address, _token_id: uint256, _data: Bytes[4096] = b""):
    """
    @notice Transfers the ownership of an NFT from one address to another address
    @dev Throws unless `msg.sender` is the current owner, an authorized
        operator, or the approved address for this NFT. Throws if `_from` is
        not the current owner. Throws if `_to` is the zero address. Throws if
        `_tokenId` is not a valid NFT. When transfer is complete, this function
        checks if `_to` is a smart contract (code size > 0). If so, it calls
        `onERC721Received` on `_to` and throws if the return value is not
        `bytes4(keccak256("onERC721Received(address,address,uint256,bytes)"))`.
    @param _from The current owner of the NFT
    @param _to The new owner
    @param _token_id The NFT to transfer
    @param _data Additional data with no specified format, sent in call to `_to`, max length 4096
    """
    assert self._is_approved_or_owner(msg.sender, _token_id)  # dev: neither owner nor approved
    self._transfer(_from, _to, _token_id)

    if _to.is_contract:
        response: bytes32 = ERC721Receiver(_to).onERC721Received(
            msg.sender, _from, _token_id, _data
        )
        assert slice(response, 0, 4) == method_id(
            "onERC721Received(address,address,uint256,bytes)"
        )  # dev: invalid response


@external
def setApprovalForAll(_operator: address, _approved: bool):
    """
    @notice Enable or disable approval for a third party ("operator") to manage
        all of `msg.sender`'s assets.
    @dev Emits the ApprovalForAll event. Multiple operators per account are allowed.
    @param _operator Address to add to the set of authorized operators.
    @param _approved True if the operator is approved, false to revoke approval.
    """
    self.isApprovedForAll[msg.sender][_operator] = _approved
    log ApprovalForAll(msg.sender, _operator, _approved)


@external
def transferFrom(_from: address, _to: address, _token_id: uint256):
    """
    @notice Transfer ownership of an NFT -- THE CALLER IS RESPONSIBLE
        TO CONFIRM THAT `_to` IS CAPABLE OF RECEIVING NFTS OR ELSE
        THEY MAY BE PERMANENTLY LOST
    @dev Throws unless `msg.sender` is the current owner, an authorized
        operator, or the approved address for this NFT. Throws if `_from` is
        not the current owner. Throws if `_to` is the ZERO_ADDRESS.
    @param _from The current owner of the NFT
    @param _to The new owner
    @param _token_id The NFT to transfer
    """
    assert self._is_approved_or_owner(msg.sender, _token_id)  # dev: neither owner nor approved
    self._transfer(_from, _to, _token_id)


@view
@external
def tokenURI(_token_id: uint256) -> String[2]:
    return ""


@external
def burn(_token_id: uint256):
    """
    @notice Destroy a token
    @dev Only callable by the token owner, their operator, or an approved account.
        Burning a token with a currently active boost, burns the boost.
    @param _token_id The token to burn
    """
    assert self._is_approved_or_owner(msg.sender, _token_id)  # dev: neither owner nor approved

    tdata: uint256 = self.boost_token[_token_id].data
    if tdata != 0:
        tslope: int256 = 0
        tbias: int256 = 0
        tbias, tslope = self._deconstruct_bias_slope(tdata)

        delegator: address = convert(shift(_token_id, -96), address)
        owner: address = self.ownerOf[_token_id]

        self._burn_boost(_token_id, delegator, owner, tbias, tslope)

        log BurnBoost(delegator, owner, _token_id)

    self._burn(_token_id)


#@ if mode == "test":
@external
def _mint_for_testing(_to: address, _token_id: uint256):
    self._mint(_to, _token_id)


@external
def _burn_for_testing(_token_id: uint256):
    self._burn(_token_id)
#@ endif


@external
def create_boost(
    _delegator: address,
    _receiver: address,
    _percentage: int256,
    _cancel_time: uint256,
    _expire_time: uint256,
    _id: uint256,
):
    """
    @notice Create a boost and delegate it to another account.
    @dev Delegated boost can become negative, and requires active management, else
        the adjusted veCRV balance of the delegator's account will decrease until reaching 0
    @param _delegator The account to delegate boost from
    @param _receiver The account to receive the delegated boost
    @param _percentage Since veCRV is a constantly decreasing asset, we use percentage to determine
        the amount of delegator's boost to delegate
    @param _cancel_time A point in time before _expire_time in which the delegator or their operator
        can cancel the delegated boost
    @param _expire_time The point in time, atleast a day in the future, at which the value of the boost
        will reach 0. After which the negative value is deducted from the delegator's account (and the
        receiver's received boost only) until it is cancelled
    @param _id The token id, within the range of [0, 2 ** 56)
    """
    assert msg.sender == _delegator or self.isApprovedForAll[_delegator][msg.sender]  # dev: only delegator or operator
    assert _percentage > 0  # dev: percentage must be greater than 0 bps
    assert _percentage <= MAX_PCT  # dev: percentage must be less than 10_000 bps
    assert _cancel_time <= _expire_time  # dev: cancel time is after expiry

    # timestamp when delegating account's voting escrow ends - also our second point (lock_expiry, 0)
    lock_expiry: uint256 = VotingEscrow(VOTING_ESCROW).locked__end(_delegator)

    assert _expire_time >= block.timestamp + MIN_DELEGATION_TIME  # dev: boost duration must be atleast MIN_DELEGATION_TIME
    assert _expire_time <= lock_expiry # dev: boost expiration is past voting escrow lock expiry
    assert _id < 2 ** 96  # dev: id out of bounds

    # [delegator address 160][cancel_time uint40][id uint56]
    token_id: uint256 = shift(convert(_delegator, uint256), 96) + _id
    # check if the token exists here before we expend more gas by minting it
    self._mint(_receiver, token_id)

    time: int256 = convert(block.timestamp, int256)
    vecrv_balance: int256 = convert(VotingEscrow(VOTING_ESCROW).balanceOf(_delegator), int256)

    # delegated slope and bias
    dslope: int256 = 0
    dbias: int256 = 0
    dbias, dslope = self._deconstruct_bias_slope(self.boost[_delegator].delegated)

    # verify delegated boost isn't negative, else it'll inflate out vecrv balance
    delegated_boost: int256 = dslope * time + dbias
    assert delegated_boost >= 0  # dev: outstanding negative boosts

    y: int256 = _percentage * (vecrv_balance - delegated_boost) / MAX_PCT
    assert y > 0  # dev: no boost

    # (y2 - y1) / (x2 - x1)
    slope: int256 = -y / convert(_expire_time - block.timestamp, int256)  # negative value
    assert slope < 0  # dev: invalid slope

    # y = mx + b -> y - mx = b
    bias: int256 = y - slope * time

    self._mint_boost(token_id, _delegator, _receiver, bias, slope, _cancel_time)

    log DelegateBoost(_delegator, _receiver, token_id, convert(y, uint256), _cancel_time, _expire_time)


@external
def extend_boost(_token_id: uint256, _percentage: int256, _expire_time: uint256, _cancel_time: uint256):
    """
    @notice Extend the boost of an existing boost or expired boost
    @dev The extension can not decrease the value of the boost. If there are
        any outstanding negative value boosts which cause the delegable boost
        of an account to be negative this call will revert
    @param _token_id The token to extend the boost of
    @param _percentage The percentage of delegable boost to delegate
        AFTER burning the token's current boost
    @param _expire_time The new time at which the boost value will become
        0, and eventually negative. Must be greater than the previous expiry time,
        and atleast a day from now, and less than the veCRV lock expiry of the
        delegator's account.
    """
    delegator: address = convert(shift(_token_id, -96), address)
    receiver: address = self.ownerOf[_token_id]

    assert msg.sender == delegator or self.isApprovedForAll[delegator][msg.sender]  # dev: only delegator or operator
    assert _percentage > 0  # dev: percentage must be greater than 0 bps
    assert _percentage <= MAX_PCT  # dev: percentage must be less than 10_000 bps

    # timestamp when delegating account's voting escrow ends - also our second point (lock_expiry, 0)
    lock_expiry: uint256 = VotingEscrow(VOTING_ESCROW).locked__end(delegator)
    token: Token = self.boost_token[_token_id]

    assert _cancel_time <= _expire_time  # dev: cancel time is after expiry
    assert _expire_time >= block.timestamp + MIN_DELEGATION_TIME  # dev: boost duration must be atleast one day
    assert _expire_time <= lock_expiry # dev: boost expiration is past voting escrow lock expiry

    time: int256 = convert(block.timestamp, int256)
    vecrv_balance: int256 = convert(VotingEscrow(VOTING_ESCROW).balanceOf(delegator), int256)

    tslope: int256 = 0
    tbias: int256 = 0
    tbias, tslope = self._deconstruct_bias_slope(token.data)
    tvalue: int256 = tslope * time + tbias

    # assert the new expiry is ahead of the already existing expiry, otherwise
    # this isn't really an extension
    token_expiry: uint256 = convert(-tbias / tslope, uint256)

    # Can extend a token by increasing it's amount but not it's expiry time
    assert _expire_time >= token_expiry  # dev: new expiration must be greater than old token expiry

    # if we are extending an unexpired boost, the cancel time must the same or greater
    # else we can adjust the cancel time to our preference
    if _cancel_time < token.cancel_time:
        assert block.timestamp > token_expiry  # dev: cancel time reduction disallowed

    self._burn_boost(_token_id, delegator, receiver, tbias, tslope)

    # delegated slope and bias
    dslope: int256 = 0
    dbias: int256 = 0
    dbias, dslope = self._deconstruct_bias_slope(self.boost[delegator].delegated)

    # verify delegated boost isn't negative, else it'll inflate out vecrv balance
    delegated_boost: int256 = dslope * time + dbias
    assert delegated_boost >= 0  # dev: outstanding negative boosts

    y: int256 = _percentage * (vecrv_balance - delegated_boost) / MAX_PCT
    assert y > 0  # dev: no boost

    assert y >= tvalue  # dev: cannot reduce value of boost

    # (y2 - y1) / (x2 - x1)
    slope: int256 = -y / convert(_expire_time - block.timestamp, int256)  # negative value
    assert slope < 0  # dev: invalid slope

    # y = mx + b -> y - mx = b
    bias: int256 = y - slope * time

    self._mint_boost(_token_id, delegator, receiver, bias, slope, _cancel_time)

    log ExtendBoost(delegator, receiver, _token_id, convert(y, uint256), _expire_time, _cancel_time)


@external
def cancel_boost(_token_id: uint256):
    """
    @notice Cancel an outstanding boost
    @dev This does not burn the token, only the boost it represents. The owner
        of the token or their operator can cancel a boost at any time. The
        delegator or their operator can only cancel a token after the cancel
        time. Anyone can cancel the boost if the value of it is negative.
    @param _token_id The token to cancel
    """
    receiver: address = self.ownerOf[_token_id]
    delegator: address = convert(shift(_token_id, -96), address)

    token: Token = self.boost_token[_token_id]
    tslope: int256 = 0
    tbias: int256 = 0
    tbias, tslope = self._deconstruct_bias_slope(token.data)
    tvalue: int256 = tslope * convert(block.timestamp, int256) + tbias

    # if not (the owner or operator or the boost value is negative)
    if not (msg.sender == receiver or self.isApprovedForAll[receiver][msg.sender] or tvalue < 0):
        if msg.sender == delegator or self.isApprovedForAll[delegator][msg.sender]:
            # if delegator or operator, wait till after cancel time
            assert token.cancel_time <= block.timestamp
        else:
            # All others are disallowed
            raise "Not allowed!"
    self._burn_boost(_token_id, delegator, receiver, tbias, tslope)

    log BurnBoost(delegator, receiver, _token_id)


@view
@external
def adjusted_balance_of(_account: address) -> uint256:
    """
    @notice Adjusted veCRV balance after accounting for delegations and boosts
    @dev If boosts/delegations have a negative value, they're effective value is 0
    @param _account The account to query the adjusted balance of
    """
    vecrv_balance: int256 = convert(VotingEscrow(VOTING_ESCROW).balanceOf(_account), int256)

    if self.is_killed:
        return convert(vecrv_balance, uint256)

    boost: Boost = self.boost[_account]
    time: int256 = convert(block.timestamp, int256)

    delegated_boost: int256 = 0
    received_boost: int256 = 0

    if boost.delegated != 0:
        dslope: int256 = 0
        dbias: int256 = 0
        dbias, dslope = self._deconstruct_bias_slope(boost.delegated)

        # we take the absolute value, since delegated boost can be negative
        # if any outstanding negative boosts are in circulation
        # this can inflate the vecrv balance of a user
        # taking the absolute value has the effect that it costs
        # a user to negatively impact another's vecrv balance
        delegated_boost = abs(dslope * time + dbias)

    if boost.received != 0:
        rslope: int256 = 0
        rbias: int256 = 0
        rbias, rslope = self._deconstruct_bias_slope(boost.received)

        # similar to delegated boost, our received boost can be negative
        # if any outstanding negative boosts are in our possession
        # However, unlike delegated boost, we do not negatively impact
        # our adjusted balance due to negative boosts. Instead we take
        # whichever is greater between 0 and the value of our received
        # boosts.
        received_boost = max(rslope * time + rbias, empty(int256))

    # adjusted balance = vecrv_balance - abs(delegated_boost) + max(received_boost, 0)
    adjusted_balance: int256 = vecrv_balance - delegated_boost + received_boost

    # since we took the absolute value of our delegated boost, it now instead of
    # becoming negative is positive, and will continue to increase ...
    # meaning if we keep a negative outstanding delegated balance for long
    # enought it will not only decrease our vecrv_balance but also our received
    # boost, however we return the maximum between our adjusted balance and 0
    # when delegating boost, received boost isn't used for determining how
    # much we can delegate.
    return convert(max(adjusted_balance, empty(int256)), uint256)


@view
@external
def delegated_boost(_account: address) -> uint256:
    """
    @notice Query the total effective delegated boost value of an account.
    @dev This value can be greater than the veCRV balance of
        an account if the account has outstanding negative
        value boosts.
    @param _account The account to query
    """
    dslope: int256 = 0
    dbias: int256 = 0
    dbias, dslope = self._deconstruct_bias_slope(self.boost[_account].delegated)
    time: int256 = convert(block.timestamp, int256)
    return convert(abs(dslope * time + dbias), uint256)


@view
@external
def received_boost(_account: address) -> uint256:
    """
    @notice Query the total effective received boost value of an account
    @dev This value can be 0, even with delegations which have a large value,
        if the account has any outstanding negative value boosts.
    @param _account The account to query
    """
    rslope: int256 = 0
    rbias: int256 = 0
    rbias, rslope = self._deconstruct_bias_slope(self.boost[_account].received)
    time: int256 = convert(block.timestamp, int256)
    return convert(max(rslope * time + rbias, empty(int256)), uint256)


@view
@external
def token_boost(_token_id: uint256) -> int256:
    """
    @notice Query the effective value of a boost
    @dev The effective value of a boost is negative after it's expiration
        date.
    @param _token_id The token id to query
    """
    tslope: int256 = 0
    tbias: int256 = 0
    tbias, tslope = self._deconstruct_bias_slope(self.boost_token[_token_id].data)
    time: int256 = convert(block.timestamp, int256)
    return tslope * time + tbias


@view
@external
def token_expiry(_token_id: uint256) -> uint256:
    """
    @notice Query the timestamp of a boost token's expiry
    @dev The effective value of a boost is negative after it's expiration
        date.
    @param _token_id The token id to query
    """
    tslope: int256 = 0
    tbias: int256 = 0
    tbias, tslope = self._deconstruct_bias_slope(self.boost_token[_token_id].data)
    # y = mx + b -> (y - b) / m = x -> (0 - b)/m = x
    return convert(-tbias/tslope, uint256)


@view
@external
def token_cancel_time(_token_id: uint256) -> uint256:
    """
    @notice Query the timestamp of a boost token's cancel time. This is
        the point at which the delegator can nullify the boost. A receiver
        can cancel a token at any point. Anyone can nullify a token's boost
        after it's expiration.
    @param _token_id The token id to query
    """
    return self.boost_token[_token_id].cancel_time


@external
def commit_transfer_ownership(_addr: address):
    """
    @notice Transfer ownership of contract to `addr`
    @param _addr Address to have ownership transferred to
    """
    assert msg.sender == self.admin  # dev: admin only
    self.future_admin = _addr


@external
def accept_transfer_ownership():
    """
    @notice Accept admin role, only callable by future admin
    """
    future_admin: address = self.future_admin
    assert msg.sender == future_admin
    self.admin = future_admin


@external
def set_killed(_killed: bool):
    """
    @notice Set the kill status of the contract
    @param _killed Kill state to put the contract in, True = killed, False = alive
    """
    assert msg.sender == self.admin
    self.is_killed = _killed
