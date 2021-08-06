def test_set_account_operator(alice, bob, ve_delegation):
    ve_delegation.setApprovalForAll(bob, True, {"from": alice})

    assert ve_delegation.isApprovedForAll(alice, bob) is True


def test_revoke_operator(alice, bob, ve_delegation):
    ve_delegation.setApprovalForAll(bob, True, {"from": alice})
    ve_delegation.setApprovalForAll(bob, False, {"from": alice})

    assert ve_delegation.isApprovedForAll(alice, bob) is False


def test_set_multiple_operators(alice, bob, charlie, dave, ve_delegation):
    operators = [bob, charlie, dave]
    for operator in operators:
        ve_delegation.setApprovalForAll(operator, True, {"from": alice})

    assert all(ve_delegation.isApprovedForAll(alice, operator) for operator in operators)


def test_approval_for_all_event_fired(alice, bob, ve_delegation):
    tx = ve_delegation.setApprovalForAll(bob, True, {"from": alice})

    assert "ApprovalForAll" in tx.events
    assert tx.events["ApprovalForAll"] == dict(_owner=alice, _operator=bob, _approved=True)
