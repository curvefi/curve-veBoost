import ape
import pytest

AMOUNT = 10**21


@pytest.mark.parametrize("idx", range(5))
def test_initial_state(accounts, veboost, ve, idx):
    account = accounts[idx]

    assert veboost.balanceOf(account) == ve.balanceOf(account)
    assert veboost.delegated_balance(account) == 0
    assert veboost.received_balance(account) == 0
    assert veboost.delegable_balance(account) == ve.balanceOf(account)


def test_boost(alice, bob, veboost, ve, lock_unlock_time):
    veboost.boost(bob, AMOUNT, lock_unlock_time, sender=alice)

    assert veboost.balanceOf(alice) == ve.balanceOf(alice) - veboost.delegated_balance(alice)
    assert veboost.delegated_balance(alice) == veboost.received_balance(bob)


@pytest.mark.parametrize("idx", range(2))
def test_boost_fails_with_invalid_target(alice, veboost, lock_unlock_time, ZERO_ADDRESS, idx):
    target = [alice, ZERO_ADDRESS][idx]
    with ape.reverts():
        veboost.boost(target, AMOUNT, lock_unlock_time, sender=alice)


def test_boost_fails_with_invalid_amount(alice, bob, veboost, lock_unlock_time):
    with ape.reverts():
        veboost.boost(bob, 0, lock_unlock_time, sender=alice)


def test_boost_fails_with_invalid_endtime_less_than_block_timestamp(alice, bob, veboost):
    with ape.reverts():
        veboost.boost(bob, AMOUNT, 0, sender=alice)


def test_boost_fails_with_invalid_endtime_not_week_start(alice, bob, veboost, lock_unlock_time):
    with ape.reverts():
        veboost.boost(bob, AMOUNT, lock_unlock_time - 1, sender=alice)


def test_boost_fails_with_invalid_endtime_greater_than_lock_end(
    alice, bob, veboost, lock_unlock_time
):
    with ape.reverts():
        veboost.boost(bob, AMOUNT, lock_unlock_time + 86400 * 7, sender=alice)


def test_boost_fails_with_invalid_amount_greater_than_delegable_balance(
    alice, bob, veboost, lock_unlock_time
):
    amount = veboost.delegable_balance(alice) + 1
    with ape.reverts():
        veboost.boost(bob, amount, lock_unlock_time, sender=alice)


def test_boost_fails_with_invalid_allowance(alice, bob, veboost, lock_unlock_time):
    with ape.reverts():
        veboost.boost(bob, AMOUNT, lock_unlock_time, alice, sender=bob)
