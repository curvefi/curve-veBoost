import pytest

DAY = 86400
WEEK = DAY * 7


@pytest.fixture(scope="session")
def alice_lock_value():
    return 1_000_000 * 10**18


@pytest.fixture
def alice_unlock_time(chain):
    # need to round down to weeks
    return ((chain.time() + DAY * 365 * 4) // WEEK) * WEEK


@pytest.fixture(scope="session")
def bob_lock_value():
    return 500_000 * 10**18


@pytest.fixture
def bob_unlock_time(chain):
    return ((chain.time() + DAY * 365 * 2) // WEEK) * WEEK


@pytest.fixture
def expire_time(alice_unlock_time, chain):
    now = chain.time()
    return ((now + (alice_unlock_time - now) // 2) // WEEK) * WEEK


@pytest.fixture
def cancel_time(expire_time):
    return expire_time - WEEK
