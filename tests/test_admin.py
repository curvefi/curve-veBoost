import brownie
import pytest


def test_commit_new_owner(alice, bob, veboost):
    veboost.commit_transfer_ownership(bob, {"from": alice})
    assert veboost.future_admin() == bob


def test_commit_new_owner_guarded(bob, veboost):
    with brownie.reverts():
        veboost.commit_transfer_ownership(bob, {"from": bob})


def test_accept_transfer_ownership(alice, bob, veboost):
    veboost.commit_transfer_ownership(bob, {"from": alice})
    veboost.accept_transfer_ownership({"from": bob})

    assert veboost.admin() == bob


def test_accept_transfer_ownership_guarded(alice, bob, veboost):
    veboost.commit_transfer_ownership(bob, {"from": alice})
    with brownie.reverts():
        veboost.accept_transfer_ownership({"from": alice})


@pytest.mark.usefixtures("boost_bob")
def test_set_killed(alice, bob, veboost):
    assert veboost.adjusted_balance_of(bob) > 0

    veboost.set_killed(True, {"from": alice})
    assert veboost.adjusted_balance_of(bob) == 0

    veboost.set_killed(False, {"from": alice})
    assert veboost.adjusted_balance_of(bob) > 0


def test_set_killed_guarded(bob, veboost):
    with brownie.reverts():
        veboost.set_killed(True, {"from": bob})

    with brownie.reverts():
        veboost.set_killed(False, {"from": bob})
