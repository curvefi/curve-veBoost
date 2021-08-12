import itertools as it
import math

import brownie
import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS

pytestmark = pytest.mark.usefixtures("lock_alice")


@pytest.mark.parametrize("is_whitelist,status,use_operator", it.product([False, True], repeat=3))
def test_create_boost_grey_list_control(
    alice, bob, charlie, alice_unlock_time, veboost, is_whitelist, status, use_operator
):
    veboost.set_delegation_status(bob, ZERO_ADDRESS, is_whitelist, {"from": bob})
    veboost.set_delegation_status(bob, alice, status, {"from": bob})

    caller = alice
    if use_operator:
        veboost.setApprovalForAll(charlie, True, {"from": alice})
        caller = charlie

    expected_outcome = not (is_whitelist ^ status)

    if expected_outcome is True:
        veboost.create_boost(alice, bob, 10_000, 0, alice_unlock_time, 0, {"from": caller})
        return

    with brownie.reverts(dev_revert_msg="dev: mint boost not allowed"):
        veboost.create_boost(alice, bob, 10_000, 0, alice_unlock_time, 0, {"from": caller})


@pytest.mark.usefixtures("boost_bob")
@pytest.mark.parametrize("is_whitelist,status,use_operator", it.product([False, True], repeat=3))
def test_extend_boost_grey_list_control(
    alice,
    bob,
    charlie,
    cancel_time,
    expire_time,
    veboost,
    is_whitelist,
    status,
    use_operator,
):
    veboost.set_delegation_status(bob, ZERO_ADDRESS, is_whitelist, {"from": bob})
    veboost.set_delegation_status(bob, alice, status, {"from": bob})

    caller = alice
    if use_operator:
        veboost.setApprovalForAll(charlie, True, {"from": alice})
        caller = charlie

    expected_outcome = not (is_whitelist ^ status)

    token = veboost.get_token_id(alice, 0)
    if expected_outcome is True:
        veboost.extend_boost(token, 10_000, expire_time, cancel_time, {"from": caller})
        assert math.isclose(veboost.token_boost(token), veboost.delegated_boost(alice))
        return

    with brownie.reverts(dev_revert_msg="dev: mint boost not allowed"):
        veboost.extend_boost(token, 10_000, expire_time, cancel_time, {"from": caller})


@pytest.mark.usefixtures("boost_bob")
@pytest.mark.parametrize("is_whitelist,status,use_operator", it.product([False, True], repeat=3))
def test_transferring_boost_grey_list_control(
    alice,
    bob,
    charlie,
    dave,
    veboost,
    is_whitelist,
    status,
    use_operator,
):
    veboost.set_delegation_status(dave, ZERO_ADDRESS, is_whitelist, {"from": dave})
    veboost.set_delegation_status(dave, alice, status, {"from": dave})

    caller = bob
    if use_operator:
        veboost.setApprovalForAll(charlie, True, {"from": bob})
        caller = charlie

    expected_outcome = not (is_whitelist ^ status)

    token = veboost.get_token_id(alice, 0)
    if expected_outcome is True:
        veboost.transferFrom(bob, dave, token, {"from": caller})
        assert veboost.received_boost(dave) > 0 and veboost.received_boost(bob) == 0
        return

    with brownie.reverts(dev_revert_msg="dev: transfer boost not allowed"):
        veboost.transferFrom(bob, dave, token, {"from": caller})


@pytest.mark.parametrize("is_whitelist,status,use_operator", it.product([False, True], repeat=3))
def test_batch_set_delegation_status(alice, accounts, veboost, is_whitelist, status, use_operator):
    caller = alice
    if use_operator:
        veboost.setApprovalForAll(accounts[1], True, {"from": alice})
        caller = accounts[1]

    delegators = [ZERO_ADDRESS] + accounts[2:]
    statuses = [is_whitelist] + [status] * len(accounts[2:])

    tx = veboost.batch_set_delegation_status(
        alice,
        delegators + [ETH_ADDRESS] * (256 - len(delegators)),
        statuses + [2] * (256 - len(statuses)),
        {"from": caller},
    )

    with brownie.multicall(block_identifier=tx.block_number):
        results = [veboost.grey_list(alice, delegator) for delegator in delegators]

    assert all(map(lambda p: p[0] == p[1], zip(statuses, results)))
    assert veboost.grey_list(alice, ETH_ADDRESS) is False


def test_batch_set_delegation_status_only_owner_operator(alice, accounts, bob, veboost):
    delegators = [ZERO_ADDRESS] + accounts[2:]
    statuses = [False] + [True] * len(accounts[2:])

    with brownie.reverts(dev_revert_msg="dev: only receiver or operator"):
        veboost.batch_set_delegation_status(
            alice,
            delegators + [ETH_ADDRESS] * (256 - len(delegators)),
            statuses + [2] * (256 - len(statuses)),
            {"from": bob},
        )
