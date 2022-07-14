import ape
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(alice, bob, veboost_v1, lock_unlock_time):
    veboost_v1.create_boost(
        alice,
        bob,
        10_000,
        lock_unlock_time - 86400 * 7,
        lock_unlock_time - 86400 * 7,
        0,
        sender=alice,
    )


def test_migrate(alice, bob, veboost, veboost_v1):
    token_id = veboost_v1.get_token_id(alice, 0)

    veboost.migrate(token_id, sender=alice)
    assert veboost.delegated_balance(alice) > 0


def test_migrate_fails_for_migrated_tokens(alice, bob, veboost, veboost_v1):
    token_id = veboost_v1.get_token_id(alice, 0)

    veboost.migrate(token_id, sender=alice)
    with ape.reverts():
        veboost.migrate(token_id, sender=alice)


def test_migrate_fails_for_expired_tokens(alice, bob, chain, veboost, veboost_v1, lock_unlock_time):
    token_id = veboost_v1.get_token_id(alice, 0)

    chain.mine(timestamp=lock_unlock_time + 1)

    with ape.reverts():
        veboost.migrate(token_id, sender=alice)
