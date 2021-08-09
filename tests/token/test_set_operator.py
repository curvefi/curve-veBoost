def test_set_account_operator(alice, bob, veboost):
    veboost.setApprovalForAll(bob, True, {"from": alice})

    assert veboost.isApprovedForAll(alice, bob) is True


def test_revoke_operator(alice, bob, veboost):
    veboost.setApprovalForAll(bob, True, {"from": alice})
    veboost.setApprovalForAll(bob, False, {"from": alice})

    assert veboost.isApprovedForAll(alice, bob) is False


def test_set_multiple_operators(alice, bob, charlie, dave, veboost):
    operators = [bob, charlie, dave]
    for operator in operators:
        veboost.setApprovalForAll(operator, True, {"from": alice})

    assert all(veboost.isApprovedForAll(alice, operator) for operator in operators)


def test_approval_for_all_event_fired(alice, bob, veboost):
    tx = veboost.setApprovalForAll(bob, True, {"from": alice})

    assert "ApprovalForAll" in tx.events
    assert tx.events["ApprovalForAll"] == dict(_owner=alice, _operator=bob, _approved=True)
