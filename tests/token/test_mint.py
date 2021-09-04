import pytest


def test_update_total_supply(alice, veboost):
    veboost._mint_for_testing(alice, 0)

    assert veboost.totalSupply() == 1


@pytest.mark.usefixtures("lock_alice")
def test_update_global_enumeration(alice, chain, veboost):
    expiry = chain.time() + 86400 * 31
    veboost.create_boost(alice, alice, 10_000, 0, expiry, 0)

    assert veboost.tokenByIndex(0) == veboost.get_token_id(alice, 0)


@pytest.mark.usefixtures("lock_alice")
def test_update_owner_enumeration(alice, bob, chain, veboost):
    expiry = chain.time() + 86400 * 31
    veboost.create_boost(alice, bob, 10_000, 0, expiry, 0)

    assert veboost.tokenOfOwnerByIndex(bob, 0) == veboost.get_token_id(alice, 0)
