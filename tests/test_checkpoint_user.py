def test_user_checkpoint(alice, bob, chain, veboost, ve, lock_unlock_time):
    veboost.boost(bob, 10**21, lock_unlock_time, sender=alice)

    a = dict(veboost.delegated(alice).items())
    chain.mine(deltatime=86400 * 7)
    veboost.checkpoint_user(alice, sender=alice)
    assert a != dict(veboost.delegated(alice).items())
