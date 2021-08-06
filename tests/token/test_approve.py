import brownie
import pytest
from brownie import ZERO_ADDRESS


@pytest.fixture(scope="module", autouse=True)
def setup(alice, ve_delegation):
    ve_delegation._mint_for_testing(alice, 0, {"from": alice})


def test_set_approved(alice, bob, ve_delegation):
    ve_delegation.approve(bob, 0, {"from": alice})

    assert ve_delegation.getApproved(0) == bob


def test_overwrite_approved(alice, bob, charlie, ve_delegation):
    ve_delegation.approve(bob, 0, {"from": alice})
    ve_delegation.approve(charlie, 0, {"from": alice})

    assert ve_delegation.getApproved(0) == charlie


def test_revoke_approval(alice, bob, ve_delegation):
    ve_delegation.approve(bob, 0, {"from": alice})
    ve_delegation.approve(ZERO_ADDRESS, 0, {"from": alice})

    assert ve_delegation.getApproved(0) == ZERO_ADDRESS


def test_operator_set_approved(alice, bob, dave, ve_delegation):
    ve_delegation.setApprovalForAll(dave, True, {"from": alice})
    ve_delegation.approve(bob, 0, {"from": dave})

    assert ve_delegation.getApproved(0) == bob


def test_operator_overwrite_approved(alice, bob, charlie, dave, ve_delegation):
    ve_delegation.setApprovalForAll(dave, True, {"from": alice})
    ve_delegation.approve(bob, 0, {"from": alice})
    ve_delegation.approve(charlie, 0, {"from": dave})

    assert ve_delegation.getApproved(0) == charlie


def test_operator_revoke_approval(alice, bob, dave, ve_delegation):
    ve_delegation.setApprovalForAll(dave, True, {"from": alice})
    ve_delegation.approve(bob, 0, {"from": alice})
    ve_delegation.approve(ZERO_ADDRESS, 0, {"from": dave})

    assert ve_delegation.getApproved(0) == ZERO_ADDRESS


def test_operator_approval_event_fired(alice, bob, dave, ve_delegation):
    ve_delegation.setApprovalForAll(dave, True, {"from": alice})
    tx = ve_delegation.approve(bob, 0, {"from": dave})

    assert "Approval" in tx.events
    assert tx.events["Approval"] == dict(_owner=alice, _approved=bob, _token_id=0)


def test_caller_not_owner_or_operator(bob, ve_delegation):
    with brownie.reverts("dev: must be owner or operator"):
        ve_delegation.approve(bob, 0, {"from": bob})
