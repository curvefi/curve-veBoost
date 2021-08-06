import brownie
import pytest
from brownie import ZERO_ADDRESS
from brownie.convert.datatypes import HexString


@pytest.fixture(scope="module", autouse=True)
def setup(alice, ve_delegation):
    ve_delegation._mint_for_testing(alice, 0, {"from": alice})


def test_transfer_token(alice, bob, ve_delegation):
    ve_delegation.safeTransferFrom(alice, bob, 0, {"from": alice})

    assert ve_delegation.ownerOf(0) == bob
    assert ve_delegation.balanceOf(alice) == 0
    assert ve_delegation.balanceOf(bob) == 1


def test_transfer_token_approved(alice, bob, ve_delegation):
    ve_delegation.approve(bob, 0, {"from": alice})
    ve_delegation.safeTransferFrom(alice, bob, 0, {"from": bob})

    assert ve_delegation.ownerOf(0) == bob


def test_transfer_token_operator(alice, bob, ve_delegation):
    ve_delegation.setApprovalForAll(bob, True, {"from": alice})
    ve_delegation.safeTransferFrom(alice, bob, 0, {"from": bob})

    assert ve_delegation.ownerOf(0) == bob


def test_safety_check_success(alice, pm, ve_delegation):
    ERC721ReceiverMock = pm("OpenZeppelin/openzeppelin-contracts@4.2.0").ERC721ReceiverMock
    ret_val = ERC721ReceiverMock.signatures["onERC721Received"]
    mock_receiver = ERC721ReceiverMock.deploy(ret_val, 0, {"from": alice})

    ve_delegation.safeTransferFrom(alice, mock_receiver, 0, {"from": alice})

    assert ve_delegation.ownerOf(0) == mock_receiver


def test_fourth_argument_passed_to_contract_in_subcall(alice, pm, ve_delegation):
    ERC721ReceiverMock = pm("OpenZeppelin/openzeppelin-contracts@4.2.0").ERC721ReceiverMock
    ret_val = ERC721ReceiverMock.signatures["onERC721Received"]
    mock_receiver = ERC721ReceiverMock.deploy(ret_val, 0, {"from": alice})

    tx = ve_delegation.safeTransferFrom(alice, mock_receiver, 0, b"Hello world!", {"from": alice})

    expected = {
        "from": ve_delegation,
        "function": "onERC721Received(address,address,uint256,bytes)",
        "inputs": {
            "data": HexString(b"Hello world!", "bytes"),
            "from": alice,
            "operator": alice,
            "tokenId": 0,
        },
        "op": "CALL",
        "to": mock_receiver,
        "value": 0,
    }

    assert tx.subcalls[0] == expected


def test_transfer_event_fires(alice, bob, ve_delegation):
    tx = ve_delegation.safeTransferFrom(alice, bob, 0, {"from": alice})

    assert "Transfer" in tx.events
    assert tx.events["Transfer"] == dict(_from=alice, _to=bob, _token_id=0)


@pytest.mark.parametrize(
    "error_code,error_message",
    zip([1, 2, 3], ["ERC721ReceiverMock: reverting", "", "Division or modulo by zero"]),
)
def test_safety_check_fail(alice, error_code, error_message, pm, ve_delegation):
    ERC721ReceiverMock = pm("OpenZeppelin/openzeppelin-contracts@4.2.0").ERC721ReceiverMock
    mock_receiver = ERC721ReceiverMock.deploy("0x00c0fFEe", error_code, {"from": alice})

    with brownie.reverts(error_message):
        ve_delegation.safeTransferFrom(alice, mock_receiver, 0, {"from": alice})


def test_neither_owner_nor_approved(alice, bob, ve_delegation):
    with brownie.reverts("dev: neither owner nor approved"):
        ve_delegation.safeTransferFrom(alice, bob, 0, {"from": bob})


def test_transfer_to_null_account_reverts(alice, ve_delegation):
    with brownie.reverts("dev: transfers to ZERO_ADDRESS are disallowed"):
        ve_delegation.safeTransferFrom(alice, ZERO_ADDRESS, 0, {"from": alice})


def test_from_address_is_not_owner(alice, bob, ve_delegation):
    with brownie.reverts("dev: _from is not owner"):
        ve_delegation.safeTransferFrom(bob, alice, 0, {"from": alice})
