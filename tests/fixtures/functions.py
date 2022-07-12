import pytest


@pytest.fixture(scope="module", autouse=True)
def lock(alice, crv, ve, lock_amount, lock_unlock_time):
    crv.approve(ve, 2**256 - 1, sender=alice)
    ve.create_lock(lock_amount, lock_unlock_time, sender=alice)
