import itertools as it
import math

import brownie
import pytest

DAY = 86400
WEEK = DAY * 7


pytestmark = pytest.mark.usefixtures("boost_bob")


@pytest.mark.parametrize("expiry_delta,cancel_delta", it.product([0, 1], repeat=2))
def test_extend_an_existing_boost_modify_(
    alice, expire_time, veboost, cancel_time, expiry_delta, cancel_delta
):
    token = veboost.get_token_id(alice, 0)
    original_boost_value = veboost.token_boost(token)
    veboost.extend_boost(
        token, 7_500, expire_time + expiry_delta, cancel_time + cancel_delta, {"from": alice}
    )

    assert math.isclose(veboost.token_boost(token), original_boost_value * 1.5, rel_tol=1e-6)
    assert veboost.token_expiry(token) == expire_time + expiry_delta
    assert veboost.token_cancel_time(token) == cancel_time + cancel_delta


def test_delegator_operator_can_extend_a_boost(alice, bob, expire_time, veboost, cancel_time):
    veboost.setApprovalForAll(bob, True, {"from": alice})

    token = veboost.get_token_id(alice, 0)
    original_boost_value = veboost.token_boost(token)
    veboost.extend_boost(token, 7_500, expire_time + 1, cancel_time + 1, {"from": alice})

    assert math.isclose(veboost.token_boost(token), original_boost_value * 1.5)
    assert veboost.token_expiry(token) == expire_time + 1
    assert veboost.token_cancel_time(token) == cancel_time + 1


def test_only_delegator_or_operator(alice, bob, expire_time, veboost, cancel_time):
    token = veboost.get_token_id(alice, 0)
    with brownie.reverts(dev_revert_msg="dev: only delegator or operator"):
        veboost.extend_boost(token, 7_500, expire_time + 1, cancel_time + 1, {"from": bob})


@pytest.mark.parametrize(
    "pct,msg",
    [
        (0, "dev: percentage must be greater than 0 bps"),
        (10_001, "dev: percentage must be less than 10_000 bps"),
    ],
)
def test_invalid_percentage(alice, expire_time, pct, msg, veboost, cancel_time):
    token = veboost.get_token_id(alice, 0)
    with brownie.reverts(msg):
        veboost.extend_boost(token, pct, expire_time + 1, cancel_time + 1, {"from": alice})


def test_new_cancel_time_must_be_less_than_new_expiry(alice, expire_time, veboost):
    token = veboost.get_token_id(alice, 0)
    with brownie.reverts(dev_revert_msg="dev: cancel time is after expiry"):
        veboost.extend_boost(token, 7_000, expire_time, expire_time + 1, {"from": alice})


def test_new_expiry_must_be_greater_than_min_delegation(alice, chain, veboost):
    token = veboost.get_token_id(alice, 0)
    with brownie.reverts(dev_revert_msg="dev: boost duration must be atleast one day"):
        veboost.extend_boost(token, 7_000, chain.time(), 0, {"from": alice})


def test_new_expiry_must_be_less_than_lock_expiry(alice, alice_unlock_time, cancel_time, veboost):
    token = veboost.get_token_id(alice, 0)
    with brownie.reverts(dev_revert_msg="dev: boost expiration is past voting escrow lock expiry"):
        veboost.extend_boost(token, 7_000, alice_unlock_time + 1, cancel_time, {"from": alice})


def test_expiry_must_be_greater_than_tokens_current_expiry(
    alice, expire_time, cancel_time, veboost
):
    token = veboost.get_token_id(alice, 0)
    with brownie.reverts(
        dev_revert_msg="dev: new expiration must be greater than old token expiry"
    ):
        veboost.extend_boost(token, 7_000, expire_time - 1, cancel_time, {"from": alice})


def test_decreasing_cancel_time_on_active_token_disallowed(
    alice, chain, expire_time, cancel_time, veboost
):
    token = veboost.get_token_id(alice, 0)
    with brownie.reverts(dev_revert_msg="dev: cancel time reduction disallowed"):
        veboost.extend_boost(token, 7_000, expire_time, cancel_time - 1, {"from": alice})

    chain.mine(timestamp=expire_time)
    veboost.extend_boost(token, 7_000, chain.time() + WEEK, cancel_time - 1, {"from": alice})


def test_outstanding_negative_boosts_prevent_extending_boosts(
    alice, charlie, chain, expire_time, cancel_time, veboost
):
    # give charlie our remaining boost
    veboost.create_boost(alice, charlie, 10_000, 0, chain.time() + WEEK, 1, {"from": alice})
    # fast forward to a day the boost given to charlie has expired
    chain.mine(timestamp=expire_time - (WEEK + DAY))

    with brownie.reverts(dev_revert_msg="dev: outstanding negative boosts"):
        veboost.extend_boost(
            veboost.get_token_id(alice, 0), 7_000, expire_time, cancel_time, {"from": alice}
        )


def test_no_boost_available_to_extend_with(
    alice,
    charlie,
    chain,
    veboost,
    alice_unlock_time,
):
    # TODO: how to make this test not fail so often?
    # need someway to make a transaction execute at an exact timestamp

    token = veboost.get_token_id(alice, 0)
    token_expiry = veboost.token_expiry(token)

    # fast forward to when the boost expires
    chain.mine(timestamp=token_expiry)

    # sometimes we get a little ganache jitter and this will hit
    # but essentially we want to know that the value of the token is
    # 0 and only 0
    assert veboost.token_boost(token) == 0

    # give charlie our remaining boost, which is actually 100% of our vecrv
    # since token 0 is valued at 0 boost
    veboost.create_boost(alice, charlie, 10_000, 0, alice_unlock_time, 1, {"from": alice})

    # forward in time some more
    chain.mine(timestamp=alice_unlock_time - WEEK - DAY)

    # we try to extend token 0, but after removing it's negative effect
    # it turns out we have no boost left to give, since token 1 has it all
    with brownie.reverts(dev_revert_msg="dev: no boost"):
        veboost.extend_boost(token, 7_000, alice_unlock_time, 0, {"from": alice})


def test_extension_cannot_result_in_a_lesser_value(alice, expire_time, cancel_time, veboost):
    token = veboost.get_token_id(alice, 0)
    with brownie.reverts(dev_revert_msg="dev: cannot reduce value of boost"):
        veboost.extend_boost(token, 2_000, expire_time, cancel_time, {"from": alice})


def test_slope_cannot_equal_zero(alice, charlie, chain, crv, vecrv, veboost):
    # slope can be equal to 0 due to integer division, as the
    # amount of boost we are delegating is divided by the length of the
    # boost period, in which case if abs(y) < boost period, the slope will be 0
    amount = (DAY * 365 * 4 // WEEK) * WEEK  # very small amount
    unlock_time = ((chain.time() + amount) // WEEK) * WEEK
    crv.transfer(charlie, amount * 10, {"from": alice})
    crv.approve(vecrv, amount * 10, {"from": charlie})
    vecrv.create_lock(amount * 10, unlock_time, {"from": charlie})
    # this should work and be okeay
    veboost.create_boost(charlie, alice, 10_000, 0, chain.time() + WEEK, 0, {"from": charlie})

    # fast forward to when we have very little boost left
    chain.mine(timestamp=unlock_time - (WEEK + DAY))
    with brownie.reverts(dev_revert_msg="dev: invalid slope"):
        veboost.extend_boost(
            veboost.get_token_id(charlie, 0), 1, chain.time() + WEEK, 0, {"from": charlie}
        )


def test_cannot_extend_non_existent_boost(alice, veboost):
    token = veboost.get_token_id(alice, 10)
    with brownie.reverts(dev_revert_msg="dev: boost token does not exist"):
        veboost.extend_boost(token, 1, 0, 0, {"from": alice})
