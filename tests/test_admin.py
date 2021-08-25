import brownie


def test_commit_new_owner(alice, bob, veboost):
    veboost.commit_transfer_ownership(bob, {"from": alice})
    assert veboost.future_admin() == bob


def test_commit_new_owner_guarded(bob, veboost):
    with brownie.reverts():
        veboost.commit_transfer_ownership(bob, {"from": bob})


def test_accept_transfer_ownership(alice, bob, veboost):
    veboost.commit_transfer_ownership(bob, {"from": alice})
    veboost.accept_transfer_ownership({"from": bob})

    assert veboost.admin() == bob


def test_accept_transfer_ownership_guarded(alice, bob, veboost):
    veboost.commit_transfer_ownership(bob, {"from": alice})
    with brownie.reverts():
        veboost.accept_transfer_ownership({"from": alice})


def test_set_base_uri(alice, veboost):
    veboost.set_base_uri("https://api.curve.fi/api/getveboost?token_id=", {"from": alice})

    # test max length
    with brownie.reverts():
        veboost.set_base_uri("a" * 129, {"from": alice})


def test_set_base_uri_guarded(bob, veboost):
    with brownie.reverts():
        veboost.set_base_uri("https://api.curve.fi/api/getveboost?token_id=", {"from": bob})
