import brownie
import pytest
from brownie import ZERO_ADDRESS


@pytest.fixture(scope="module", autouse=True)
def setup(alice, veboost):
    veboost._mint_for_testing(alice, 0, {"from": alice})


def test_transfer_token(alice, bob, veboost):
    veboost.transferFrom(alice, bob, 0, {"from": alice})

    assert veboost.ownerOf(0) == bob
    assert veboost.balanceOf(alice) == 0
    assert veboost.balanceOf(bob) == 1


def test_transfer_token_approved(alice, bob, veboost):
    veboost.approve(bob, 0, {"from": alice})
    veboost.transferFrom(alice, bob, 0, {"from": bob})

    assert veboost.ownerOf(0) == bob


def test_transfer_token_operator(alice, bob, veboost):
    veboost.setApprovalForAll(bob, True, {"from": alice})
    veboost.transferFrom(alice, bob, 0, {"from": bob})

    assert veboost.ownerOf(0) == bob


def test_no_safety_check(alice, veboost):
    veboost.transferFrom(alice, veboost, 0, {"from": alice})

    assert veboost.ownerOf(0) == veboost


def test_transfer_event_fires(alice, bob, veboost):
    tx = veboost.transferFrom(alice, bob, 0, {"from": alice})

    assert "Transfer" in tx.events
    assert tx.events["Transfer"] == dict(_from=alice, _to=bob, _token_id=0)


def test_transfer_updates_enumerations(alice, bob, veboost):
    veboost._mint_for_testing(alice, 10_000, {"from": alice})
    veboost.transferFrom(alice, bob, 10_000, {"from": alice})

    assert veboost.tokenByIndex(0) == 0
    assert veboost.tokenByIndex(1) == 10_000
    assert veboost.tokenOfOwnerByIndex(alice, 0) == 0
    assert veboost.tokenOfOwnerByIndex(alice, 1) == 0
    assert veboost.tokenOfOwnerByIndex(bob, 0) == 10_000
    assert veboost.totalSupply() == 2


def test_neither_owner_nor_approved(alice, bob, veboost):
    with brownie.reverts(dev_revert_msg="dev: neither owner nor approved"):
        veboost.transferFrom(alice, bob, 0, {"from": bob})


def test_transfer_to_null_account_reverts(alice, veboost):
    with brownie.reverts(dev_revert_msg="dev: transfers to ZERO_ADDRESS are disallowed"):
        veboost.transferFrom(alice, ZERO_ADDRESS, 0, {"from": alice})


def test_from_address_is_not_owner(alice, bob, veboost):
    with brownie.reverts(dev_revert_msg="dev: _from is not owner"):
        veboost.transferFrom(bob, alice, 0, {"from": alice})
