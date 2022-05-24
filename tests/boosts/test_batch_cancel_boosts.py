import itertools as it

import brownie
import pytest

DAY = 86400
WEEK = DAY * 7


pytestmark = pytest.mark.usefixtures("lock_alice")


@pytest.mark.parametrize("use_operator,timedelta_bps", it.product([False, True], range(0, 110, 50)))
def test_receiver_can_cancel_at_anytime(
    alice, bob, charlie, chain, alice_unlock_time, veboost, use_operator, timedelta_bps
):
    for i in range(10):
        veboost.create_boost(alice, bob, 1_000, 0, alice_unlock_time, i, {"from": alice})

    caller = bob
    if use_operator:
        veboost.setApprovalForAll(charlie, True, {"from": bob})
        caller = charlie

    fast_forward_amount = int((alice_unlock_time - chain.time()) * (timedelta_bps / 100))
    chain.mine(timedelta=fast_forward_amount)

    with brownie.multicall(block_identifier=chain.height):
        tokens = [veboost.get_token_id(alice, i) for i in range(10)]
    tx = veboost.batch_cancel_boosts(tokens + [0] * (256 - len(tokens)), {"from": caller})
    with brownie.multicall(block_identifier=tx.block_number):
        boost_values = [veboost.token_boost(token) for token in tokens]
    assert max(boost_values) == 0


@pytest.mark.parametrize("use_operator,timedelta_bps", it.product([False, True], range(0, 130, 20)))
def test_delegator_can_cancel_after_cancel_time_or_expiry(
    alice, bob, charlie, chain, alice_unlock_time, veboost, use_operator, timedelta_bps
):

    for i in range(10):
        veboost.create_boost(
            alice,
            bob,
            1_000,
            alice_unlock_time - (WEEK * i**2),
            alice_unlock_time,
            i,
            {"from": alice},
        )

    caller = alice
    if use_operator:
        veboost.setApprovalForAll(charlie, True, {"from": alice})
        caller = charlie

    fast_forward_amount = int((alice_unlock_time - chain.time()) * (timedelta_bps / 100))

    chain.mine(timedelta=fast_forward_amount)

    with brownie.multicall(block_identifier=chain.height):
        tokens = [veboost.get_token_id(alice, i) for i in range(10)]
        cancel_times = [veboost.token_cancel_time(token) for token in tokens]

    if chain.time() < max(cancel_times):
        with brownie.reverts(dev_revert_msg="dev: must wait for cancel time"):
            veboost.batch_cancel_boosts(tokens + [0] * 246, {"from": caller})
    else:
        tx = veboost.batch_cancel_boosts(tokens + [0] * 246, {"from": caller})
        with brownie.multicall(block_identifier=tx.block_number):
            boost_values = [veboost.token_boost(token) for token in tokens]
        assert max(boost_values) == 0


@pytest.mark.parametrize("timedelta_bps", range(0, 130, 30))
def test_third_parties_can_only_cancel_past_expiry(
    alice, bob, charlie, chain, alice_unlock_time, veboost, timedelta_bps
):

    for i in range(10):
        veboost.create_boost(
            alice,
            bob,
            1_000,
            0,
            alice_unlock_time - (WEEK * i**2),
            i,
            {"from": alice},
        )

    fast_forward_amount = int((alice_unlock_time - chain.time()) * (timedelta_bps / 100))

    chain.mine(timedelta=fast_forward_amount)

    with brownie.multicall(block_identifier=chain.height):
        tokens = [veboost.get_token_id(alice, i) for i in range(10)]
        expiry_times = [veboost.token_expiry(token) for token in tokens]

    if chain.time() < max(expiry_times):
        with brownie.reverts("Not allowed!"):
            veboost.batch_cancel_boosts(tokens + [0] * 246, {"from": charlie})
    else:
        tx = veboost.batch_cancel_boosts(tokens + [0] * 246, {"from": charlie})
        with brownie.multicall(block_identifier=tx.block_number):
            boost_values = [veboost.token_boost(token) for token in tokens]
        assert max(boost_values) == 0
