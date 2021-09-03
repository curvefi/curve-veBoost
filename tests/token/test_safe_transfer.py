import brownie
import pytest
from brownie import ZERO_ADDRESS
from brownie.convert.datatypes import HexString


@pytest.fixture(autouse=True)
def setup(alice, chain, veboost, alice_unlock_time, lock_alice):
    veboost.create_boost(alice, alice, 5000, 0, chain.time() + 86400 * 31, 0, {"from": alice})


def test_transfer_token(alice, bob, veboost):
    token_id = veboost.get_token_id(alice, 0)
    veboost.safeTransferFrom(alice, bob, token_id, {"from": alice})

    assert veboost.ownerOf(token_id) == bob
    assert veboost.balanceOf(alice) == 0
    assert veboost.balanceOf(bob) == 1


def test_transfer_token_approved(alice, bob, veboost):
    token_id = veboost.get_token_id(alice, 0)
    veboost.approve(bob, token_id, {"from": alice})
    veboost.safeTransferFrom(alice, bob, token_id, {"from": bob})

    assert veboost.ownerOf(token_id) == bob


def test_transfer_token_operator(alice, bob, veboost):
    token_id = veboost.get_token_id(alice, 0)
    veboost.setApprovalForAll(bob, True, {"from": alice})
    veboost.safeTransferFrom(alice, bob, token_id, {"from": bob})

    assert veboost.ownerOf(token_id) == bob


def test_safety_check_success(alice, pm, veboost):
    ERC721ReceiverMock = pm("OpenZeppelin/openzeppelin-contracts@4.2.0").ERC721ReceiverMock
    ret_val = ERC721ReceiverMock.signatures["onERC721Received"]
    mock_receiver = ERC721ReceiverMock.deploy(ret_val, 0, {"from": alice})

    token_id = veboost.get_token_id(alice, 0)

    veboost.safeTransferFrom(alice, mock_receiver, token_id, {"from": alice})

    assert veboost.ownerOf(token_id) == mock_receiver


def test_fourth_argument_passed_to_contract_in_subcall(alice, pm, veboost):
    ERC721ReceiverMock = pm("OpenZeppelin/openzeppelin-contracts@4.2.0").ERC721ReceiverMock
    ret_val = ERC721ReceiverMock.signatures["onERC721Received"]
    mock_receiver = ERC721ReceiverMock.deploy(ret_val, 0, {"from": alice})

    token_id = veboost.get_token_id(alice, 0)
    tx = veboost.safeTransferFrom(alice, mock_receiver, token_id, b"Hello world!", {"from": alice})

    expected = {
        "from": veboost,
        "function": "onERC721Received(address,address,uint256,bytes)",
        "inputs": {
            "data": HexString(b"Hello world!", "bytes"),
            "from": alice,
            "operator": alice,
            "tokenId": token_id,
        },
        "op": "CALL",
        "to": mock_receiver,
        "value": 0,
    }

    assert tx.subcalls[0] == expected


def test_transfer_event_fires(alice, bob, veboost):
    token_id = veboost.get_token_id(alice, 0)
    tx = veboost.safeTransferFrom(alice, bob, token_id, {"from": alice})

    assert "Transfer" in tx.events
    assert tx.events["Transfer"] == dict(_from=alice, _to=bob, _token_id=token_id)


@pytest.mark.parametrize(
    "error_code,error_message",
    zip([1, 2, 3], ["ERC721ReceiverMock: reverting", "", "Division or modulo by zero"]),
)
def test_safety_check_fail(alice, error_code, error_message, pm, veboost):
    ERC721ReceiverMock = pm("OpenZeppelin/openzeppelin-contracts@4.2.0").ERC721ReceiverMock
    mock_receiver = ERC721ReceiverMock.deploy("0x00c0fFEe", error_code, {"from": alice})

    token_id = veboost.get_token_id(alice, 0)
    with brownie.reverts(error_message):
        veboost.safeTransferFrom(alice, mock_receiver, token_id, {"from": alice})


def test_neither_owner_nor_approved(alice, bob, veboost):
    token_id = veboost.get_token_id(alice, 0)

    with brownie.reverts(dev_revert_msg="dev: neither owner nor approved"):
        veboost.safeTransferFrom(alice, bob, token_id, {"from": bob})


def test_transfer_to_null_account_reverts(alice, veboost):
    token_id = veboost.get_token_id(alice, 0)

    with brownie.reverts(dev_revert_msg="dev: transfers to ZERO_ADDRESS are disallowed"):
        veboost.safeTransferFrom(alice, ZERO_ADDRESS, token_id, {"from": alice})


def test_from_address_is_not_owner(alice, bob, veboost):
    token_id = veboost.get_token_id(alice, 0)

    with brownie.reverts(dev_revert_msg="dev: _from is not owner"):
        veboost.safeTransferFrom(bob, alice, token_id, {"from": alice})
