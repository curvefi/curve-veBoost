import pytest


@pytest.fixture
def lock_alice(alice, alice_lock_value, alice_unlock_time, crv, vecrv):
    crv.approve(vecrv, alice_lock_value, {"from": alice})
    vecrv.create_lock(alice_lock_value, alice_unlock_time, {"from": alice})


@pytest.fixture
def lock_bob(alice, bob, bob_lock_value, bob_unlock_time, crv, vecrv):
    crv.transfer(bob, bob_lock_value, {"from": alice})
    crv.approve(vecrv, bob_lock_value, {"from": bob})
    vecrv.create_lock(bob_lock_value, bob_unlock_time, {"from": bob})
