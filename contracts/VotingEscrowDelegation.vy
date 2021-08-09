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


struct Boost:
    # [bias uint128][slope uint128]
    delegated: uint256
    received: uint256


MAX_PCT: constant(uint256) = 10_000
MIN_DELEGATION_TIME: constant(uint256) = 86400
VOTING_ESCROW: constant(address) = 0x0000000000000000000000000000000000000000


balanceOf: public(HashMap[address, uint256])
getApproved: public(HashMap[uint256, address])
isApprovedForAll: public(HashMap[address, HashMap[address, bool]])
ownerOf: public(HashMap[uint256, address])

name: public(String[32])
symbol: public(String[32])

boost: HashMap[address, Boost]
boost_token: HashMap[uint256, uint256]


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
def _mint_boost(_token_id: uint256, _delegator: address, _receiver: address, _bias: int256, _slope: int256):
    data: uint256 = shift(convert(_bias, uint256), 128) + convert(abs(_slope), uint256)
    self.boost[_delegator].delegated += data
    self.boost[_receiver].received += data
    self.boost_token[_token_id] = data


@internal
def _burn_boost(_token_id: uint256, _delegator: address, _receiver: address, _bias: int256, _slope: int256):
    data: uint256 = shift(convert(_bias, uint256), 128) + convert(abs(_slope), uint256)
    self.boost[_delegator].delegated -= data
    self.boost[_receiver].received -= data
    self.boost_token[_token_id] = 0


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

    bias: int256 = 0
    slope: int256 = 0
    bias, slope = self._deconstruct_bias_slope(self.boost_token[_token_id])

    # if the boost value is negative, reset the slope and bias
    if slope * convert(block.timestamp, int256) + bias > 0:
        self._transfer_boost(_from, _to, bias, slope)
    else:
        self._burn_boost(_token_id, convert(shift(_token_id, -96), address), _from, bias, slope)

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

#@ if is_test:

@external
def _mint_for_testing(_to: address, _token_id: uint256):
    self._mint(_to, _token_id)

@external
def _burn_for_testing(_token_id: uint256):
    self._burn(_token_id)

#@ endif

@view
@external
def tokenURI(_token_id: uint256) -> String[2]:
    return ""


@external
def delegate_boost(
    _delegator: address,
    _receiver: address,
    _percentage: int256,
    _cancel_time: uint256,
    _expire_time: uint256,
    _id: uint256,
):
    assert msg.sender == _delegator or self.isApprovedForAll[_delegator][msg.sender]  # dev: only delegator or operator
    assert _percentage > 0  # dev: percentage must be greater than 0 bps
    assert _percentage <= MAX_PCT  # dev: percentage must be less than 10_000 bps
    assert _cancel_time <= _expire_time  # dev: cancel time is after expiry

    # timstamp when delegating account's voting escrow ends - also our second point (lock_expiry, 0)
    lock_expiry: uint256 = VotingEscrow(VOTING_ESCROW).locked__end(_delegator)

    assert _expire_time >= block.timestamp + MIN_DELEGATION_TIME  # dev: boost duration must be atleast one day
    assert _expire_time <= lock_expiry # dev: boost expiration is past voting escrow lock expiry
    assert _id < 2 ** 56  # dev: id out of bounds

    # [delegator address 160][cancel_time uint40][id uint56]
    token_id: uint256 = shift(convert(_delegator, uint256), 96) + shift(_cancel_time, 56) + _id
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

    self._mint_boost(token_id, _delegator, _receiver, bias, slope)
