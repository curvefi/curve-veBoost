import brownie
import pytest
from brownie import ZERO_ADDRESS
from brownie.convert.datatypes import HexString


@pytest.fixture(scope="module", autouse=True)
def setup(alice, veboost):
    veboost._mint_for_testing(alice, 0, {"from": alice})


def test_transfer_token(alice, bob, veboost):
    veboost.safeTransferFrom(alice, bob, 0, {"from": alice})

    assert veboost.ownerOf(0) == bob
    assert veboost.balanceOf(alice) == 0
    assert veboost.balanceOf(bob) == 1


def test_transfer_token_approved(alice, bob, veboost):
    veboost.approve(bob, 0, {"from": alice})
    veboost.safeTransferFrom(alice, bob, 0, {"from": bob})

    assert veboost.ownerOf(0) == bob


def test_transfer_token_operator(alice, bob, veboost):
    veboost.setApprovalForAll(bob, True, {"from": alice})
    veboost.safeTransferFrom(alice, bob, 0, {"from": bob})

    assert veboost.ownerOf(0) == bob


def test_safety_check_success(alice, pm, veboost):
    ERC721ReceiverMock = pm("OpenZeppelin/openzeppelin-contracts@4.2.0").ERC721ReceiverMock
    ret_val = ERC721ReceiverMock.signatures["onERC721Received"]
    mock_receiver = ERC721ReceiverMock.deploy(ret_val, 0, {"from": alice})

    veboost.safeTransferFrom(alice, mock_receiver, 0, {"from": alice})

    assert veboost.ownerOf(0) == mock_receiver


def test_fourth_argument_passed_to_contract_in_subcall(alice, pm, veboost):
    ERC721ReceiverMock = pm("OpenZeppelin/openzeppelin-contracts@4.2.0").ERC721ReceiverMock
    ret_val = ERC721ReceiverMock.signatures["onERC721Received"]
    mock_receiver = ERC721ReceiverMock.deploy(ret_val, 0, {"from": alice})

    tx = veboost.safeTransferFrom(alice, mock_receiver, 0, b"Hello world!", {"from": alice})

    expected = {
        "from": veboost,
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


def test_transfer_event_fires(alice, bob, veboost):
    tx = veboost.safeTransferFrom(alice, bob, 0, {"from": alice})

    assert "Transfer" in tx.events
    assert tx.events["Transfer"] == dict(_from=alice, _to=bob, _token_id=0)


@pytest.mark.parametrize(
    "error_code,error_message",
    zip([1, 2, 3], ["ERC721ReceiverMock: reverting", "", "Division or modulo by zero"]),
)
def test_safety_check_fail(alice, error_code, error_message, pm, veboost):
    ERC721ReceiverMock = pm("OpenZeppelin/openzeppelin-contracts@4.2.0").ERC721ReceiverMock
    mock_receiver = ERC721ReceiverMock.deploy("0x00c0fFEe", error_code, {"from": alice})

    with brownie.reverts(error_message):
        veboost.safeTransferFrom(alice, mock_receiver, 0, {"from": alice})


def test_neither_owner_nor_approved(alice, bob, veboost):
    with brownie.reverts("dev: neither owner nor approved"):
        veboost.safeTransferFrom(alice, bob, 0, {"from": bob})


def test_transfer_to_null_account_reverts(alice, veboost):
    with brownie.reverts("dev: transfers to ZERO_ADDRESS are disallowed"):
        veboost.safeTransferFrom(alice, ZERO_ADDRESS, 0, {"from": alice})


def test_from_address_is_not_owner(alice, bob, veboost):
    with brownie.reverts("dev: _from is not owner"):
        veboost.safeTransferFrom(bob, alice, 0, {"from": alice})
