import brownie
import pytest
from brownie import ZERO_ADDRESS


@pytest.fixture(scope="module", autouse=True)
def setup(alice, ve_delegation):
    ve_delegation._mint_for_testing(alice, 0, {"from": alice})


def test_transfer_token(alice, bob, ve_delegation):
    ve_delegation.transferFrom(alice, bob, 0, {"from": alice})

    assert ve_delegation.ownerOf(0) == bob
    assert ve_delegation.balanceOf(alice) == 0
    assert ve_delegation.balanceOf(bob) == 1


def test_transfer_token_approved(alice, bob, ve_delegation):
    ve_delegation.approve(bob, 0, {"from": alice})
    ve_delegation.transferFrom(alice, bob, 0, {"from": bob})

    assert ve_delegation.ownerOf(0) == bob


def test_transfer_token_operator(alice, bob, ve_delegation):
    ve_delegation.setApprovalForAll(bob, True, {"from": alice})
    ve_delegation.transferFrom(alice, bob, 0, {"from": bob})

    assert ve_delegation.ownerOf(0) == bob


def test_no_safety_check(alice, ve_delegation):
    ve_delegation.transferFrom(alice, ve_delegation, 0, {"from": alice})

    assert ve_delegation.ownerOf(0) == ve_delegation


def test_transfer_event_fires(alice, bob, ve_delegation):
    tx = ve_delegation.transferFrom(alice, bob, 0, {"from": alice})

    assert "Transfer" in tx.events
    assert tx.events["Transfer"] == dict(_from=alice, _to=bob, _token_id=0)


def test_neither_owner_nor_approved(alice, bob, ve_delegation):
    with brownie.reverts("dev: neither owner nor approved"):
        ve_delegation.transferFrom(alice, bob, 0, {"from": bob})


def test_transfer_to_null_account_reverts(alice, ve_delegation):
    with brownie.reverts("dev: transfers to ZERO_ADDRESS are disallowed"):
        ve_delegation.transferFrom(alice, ZERO_ADDRESS, 0, {"from": alice})


def test_from_address_is_not_owner(alice, bob, ve_delegation):
    with brownie.reverts("dev: _from is not owner"):
        ve_delegation.transferFrom(bob, alice, 0, {"from": alice})
