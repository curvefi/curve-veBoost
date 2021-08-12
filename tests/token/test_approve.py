import brownie
import pytest
from brownie import ZERO_ADDRESS


@pytest.fixture(scope="module", autouse=True)
def setup(alice, veboost):
    veboost._mint_for_testing(alice, 0, {"from": alice})


def test_set_approved(alice, bob, veboost):
    veboost.approve(bob, 0, {"from": alice})

    assert veboost.getApproved(0) == bob


def test_overwrite_approved(alice, bob, charlie, veboost):
    veboost.approve(bob, 0, {"from": alice})
    veboost.approve(charlie, 0, {"from": alice})

    assert veboost.getApproved(0) == charlie


def test_revoke_approval(alice, bob, veboost):
    veboost.approve(bob, 0, {"from": alice})
    veboost.approve(ZERO_ADDRESS, 0, {"from": alice})

    assert veboost.getApproved(0) == ZERO_ADDRESS


def test_operator_set_approved(alice, bob, dave, veboost):
    veboost.setApprovalForAll(dave, True, {"from": alice})
    veboost.approve(bob, 0, {"from": dave})

    assert veboost.getApproved(0) == bob


def test_operator_overwrite_approved(alice, bob, charlie, dave, veboost):
    veboost.setApprovalForAll(dave, True, {"from": alice})
    veboost.approve(bob, 0, {"from": alice})
    veboost.approve(charlie, 0, {"from": dave})

    assert veboost.getApproved(0) == charlie


def test_operator_revoke_approval(alice, bob, dave, veboost):
    veboost.setApprovalForAll(dave, True, {"from": alice})
    veboost.approve(bob, 0, {"from": alice})
    veboost.approve(ZERO_ADDRESS, 0, {"from": dave})

    assert veboost.getApproved(0) == ZERO_ADDRESS


def test_operator_approval_event_fired(alice, bob, dave, veboost):
    veboost.setApprovalForAll(dave, True, {"from": alice})
    tx = veboost.approve(bob, 0, {"from": dave})

    assert "Approval" in tx.events
    assert tx.events["Approval"] == dict(_owner=alice, _approved=bob, _token_id=0)


def test_caller_not_owner_or_operator(bob, veboost):
    with brownie.reverts(dev_revert_msg="dev: must be owner or operator"):
        veboost.approve(bob, 0, {"from": bob})
