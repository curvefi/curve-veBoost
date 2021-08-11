import brownie
import pytest

pytestmark = pytest.mark.usefixtures("boost_bob")


@pytest.mark.parametrize("use_operator", [False, True])
def test_burning_token(alice, bob, charlie, veboost, use_operator):
    caller = bob
    if use_operator:
        veboost.setApprovalForAll(charlie, True, {"from": bob})
        caller = charlie

    token_id = veboost.get_token_id(alice, 0)
    veboost.burn(token_id, {"from": caller})
    assert veboost.token_boost(token_id) == 0


@pytest.mark.parametrize("idx", [0] + list(range(2, 5)))
def test_third_party_cannot_burn_token(alice, accounts, veboost, idx):
    token_id = veboost.get_token_id(alice, 0)
    with brownie.reverts("dev: neither owner nor approved"):
        veboost.burn(token_id, {"from": accounts[idx]})


def test_delegator_can_remint_token_id(alice, bob, cancel_time, expire_time, veboost):
    token_id = veboost.get_token_id(alice, 0)
    veboost.burn(token_id, {"from": bob})

    veboost.create_boost(alice, bob, 10_000, cancel_time, expire_time, 0, {"from": alice})

    assert veboost.token_boost(token_id) > 0
