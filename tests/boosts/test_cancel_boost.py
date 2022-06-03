import itertools as it

import brownie
import pytest

DAY = 86400
WEEK = DAY * 7

pytestmark = pytest.mark.usefixtures("boost_bob")


@pytest.mark.parametrize("use_operator,timedelta_bps", it.product([False, True], range(0, 110, 50)))
def test_receiver_can_cancel_at_anytime(
    alice, bob, charlie, chain, expire_time, veboost, use_operator, timedelta_bps
):
    caller = bob
    if use_operator:
        veboost.setApprovalForAll(charlie, True, {"from": bob})
        caller = charlie

    fast_forward_amount = int((expire_time - chain.time()) * (timedelta_bps / 100))
    chain.mine(timedelta=fast_forward_amount)

    token = veboost.get_token_id(alice, 0)
    veboost.cancel_boost(token, {"from": caller})
    assert veboost.token_boost(token) == 0


@pytest.mark.parametrize("use_operator,timedelta_bps", it.product([False, True], range(0, 130, 20)))
def test_delegator_can_cancel_after_cancel_time_or_expiry(
    alice, charlie, chain, expire_time, cancel_time, veboost, use_operator, timedelta_bps
):
    caller = alice
    if use_operator:
        veboost.setApprovalForAll(charlie, True, {"from": alice})
        caller = charlie

    fast_forward_amount = int((expire_time - chain.time()) * (timedelta_bps / 100))

    chain.mine(timedelta=fast_forward_amount)
    token = veboost.get_token_id(alice, 0)

    if chain.time() < cancel_time:
        with brownie.reverts(dev_revert_msg="dev: must wait for cancel time"):
            veboost.cancel_boost(token, {"from": caller})
    else:
        veboost.cancel_boost(token, {"from": caller})
        assert veboost.token_boost(token) == 0


@pytest.mark.parametrize("timedelta_bps", range(0, 130, 30))
def test_third_parties_can_only_cancel_past_expiry(
    alice, charlie, chain, expire_time, veboost, timedelta_bps
):

    fast_forward_amount = int((expire_time - chain.time()) * (timedelta_bps / 100))

    chain.mine(timedelta=fast_forward_amount)
    token = veboost.get_token_id(alice, 0)

    if chain.time() < expire_time:
        with brownie.reverts("Not allowed!"):
            veboost.cancel_boost(token, {"from": charlie})
    else:
        veboost.cancel_boost(token, {"from": charlie})
        assert veboost.token_boost(token) == 0


def test_cancel_non_existent_boost_reverts(alice, veboost):

    with brownie.reverts(dev_revert_msg="dev: token does not exist"):
        veboost.cancel_boost(veboost.get_token_id(alice, 10), {"from": alice})


def test_cancel_boost_after_previous_expires(
    alice, charlie, dave, chain, alice_unlock_time, veboost, cancel_time, expire_time
):

    veboost.create_boost(
        alice, charlie, 1_000, cancel_time + WEEK, expire_time + WEEK, 1, {"from": alice}
    )

    token_bob = veboost.get_token_id(alice, 0)
    token_bob_expiry = veboost.token_expiry(token_bob)

    # go to bob's expiry
    chain.mine(timestamp=token_bob_expiry + 1)
    assert veboost.token_boost(token_bob) < 0  # in principle this should become negative
    veboost.cancel_boost(token_bob, {"from": alice})  # anyone can cancel boost position if negative
