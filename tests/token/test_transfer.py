import brownie
import pytest
from brownie import ZERO_ADDRESS


@pytest.fixture(autouse=True)
def setup(alice, chain, veboost, alice_unlock_time, lock_alice):
    veboost.create_boost(alice, alice, 5000, 0, chain.time() + 86400 * 31, 0, {"from": alice})


def test_transfer_token(alice, bob, veboost):
    token_id = veboost.get_token_id(alice, 0)
    veboost.transferFrom(alice, bob, token_id, {"from": alice})

    assert veboost.ownerOf(token_id) == bob
    assert veboost.balanceOf(alice) == 0
    assert veboost.balanceOf(bob) == 1


def test_transfer_token_approved(alice, bob, veboost):
    token_id = veboost.get_token_id(alice, 0)
    veboost.approve(bob, token_id, {"from": alice})
    veboost.transferFrom(alice, bob, token_id, {"from": bob})

    assert veboost.ownerOf(token_id) == bob


def test_transfer_token_operator(alice, bob, veboost):
    token_id = veboost.get_token_id(alice, 0)
    veboost.setApprovalForAll(bob, True, {"from": alice})
    veboost.transferFrom(alice, bob, token_id, {"from": bob})

    assert veboost.ownerOf(token_id) == bob


def test_no_safety_check(alice, veboost):
    token_id = veboost.get_token_id(alice, 0)
    veboost.transferFrom(alice, veboost, token_id, {"from": alice})

    assert veboost.ownerOf(token_id) == veboost


def test_transfer_event_fires(alice, bob, veboost):
    token_id = veboost.get_token_id(alice, 0)
    tx = veboost.transferFrom(alice, bob, token_id, {"from": alice})

    assert "Transfer" in tx.events
    assert tx.events["Transfer"] == dict(_from=alice, _to=bob, _token_id=token_id)


def test_transfer_updates_enumerations(alice, bob, chain, veboost):
    token_id = veboost.get_token_id(alice, 10_000)
    veboost.create_boost(
        alice, alice, 10_000, 0, chain.time() + 86400 * 31, 10_000, {"from": alice}
    )
    veboost.transferFrom(alice, bob, token_id, {"from": alice})

    assert veboost.tokenByIndex(0) == veboost.get_token_id(alice, 0)
    assert veboost.tokenByIndex(1) == token_id
    assert veboost.tokenOfOwnerByIndex(alice, 0) == veboost.get_token_id(alice, 0)
    assert veboost.tokenOfOwnerByIndex(alice, 1) == 0
    assert veboost.tokenOfOwnerByIndex(bob, 0) == token_id
    assert veboost.totalSupply() == 2


def test_neither_owner_nor_approved(alice, bob, veboost):
    with brownie.reverts(dev_revert_msg="dev: neither owner nor approved"):
        token_id = veboost.get_token_id(alice, 0)
        veboost.transferFrom(alice, bob, token_id, {"from": bob})


def test_transfer_to_null_account_reverts(alice, veboost):
    with brownie.reverts(dev_revert_msg="dev: transfers to ZERO_ADDRESS are disallowed"):
        token_id = veboost.get_token_id(alice, 0)
        veboost.transferFrom(alice, ZERO_ADDRESS, token_id, {"from": alice})


def test_from_address_is_not_owner(alice, bob, veboost):
    with brownie.reverts(dev_revert_msg="dev: _from is not owner"):
        token_id = veboost.get_token_id(alice, 0)
        veboost.transferFrom(bob, alice, token_id, {"from": alice})
