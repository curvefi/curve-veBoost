import pytest


@pytest.fixture(autouse=True)
def setup(alice, bob, veboost, alice_unlock_time, lock_alice):
    veboost.create_boost(
        alice, bob, 10_000, alice_unlock_time, alice_unlock_time, 0, {"from": alice}
    )


def test_update_total_supply(alice, veboost):
    veboost._burn_for_testing(veboost.get_token_id(alice, 0), {"from": alice})
    assert veboost.totalSupply() == 0


def test_update_global_enumeration(alice, veboost):
    veboost._burn_for_testing(veboost.get_token_id(alice, 0), {"from": alice})

    assert veboost.tokenByIndex(0) == 0


def test_update_owner_enumeration(alice, bob, veboost):
    veboost._burn_for_testing(veboost.get_token_id(alice, 0), {"from": alice})

    assert veboost.tokenOfOwnerByIndex(bob, 0) == 0
