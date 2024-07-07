import ape
from ape import chain
import pytest

AMOUNT = 10**21
DAY = 86400
WEEK = DAY * 7
YEAR = DAY * 365

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


def test_boost_via_approval(alice, bob, veboost, ve, lock_unlock_time):
    veboost.approve(bob, 2**256 - 1, sender=alice)
    veboost.boost(bob, AMOUNT, lock_unlock_time, alice, sender=bob)

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

def test_adjusted_balance_of_write(alice, bob, veboost, ve, lock_unlock_time):
    balance = ve.balanceOf(alice)
    amount = balance / 4
    
    # Delegate to bob
    veboost.boost(bob, int(amount), lock_unlock_time, sender=alice)

    delegated_point = veboost.delegated(alice)
    received_point = veboost.received(alice)
    
    for i in range(10):
        tx = veboost.adjusted_balance_of_write(alice, sender=bob)
        delegable = veboost.delegable_balance(alice)
        delegated = veboost.delegated_balance(alice)
        ve_balance = ve.balanceOf(alice)
        
        # Verify new point has been written (checkpoint)
        new_point = veboost.delegated(alice)
        assert new_point.ts > delegated_point.ts
        delegated_point = new_point

        new_point = veboost.received(alice)
        assert new_point.ts > received_point.ts
        received_point = new_point
        
        # Invariant: VE balance is always the sum of delegable + delegated
        assert ve_balance == delegable + delegated
        assert veboost.balanceOf(alice) == tx.return_value == delegable

        # Ensure bob's adjusted balance is equal to what Alice has delegated
        tx = veboost.adjusted_balance_of_write(bob, sender=bob)
        assert tx.return_value == veboost.balanceOf(bob)
        assert veboost.delegated_balance(alice) == veboost.balanceOf(bob)
        assert veboost.delegable_balance(bob) == 0 # Bob doesn't have any VE balance

        chain.pending_timestamp += DAY * i
        chain.mine()