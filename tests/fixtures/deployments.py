import pytest


@pytest.fixture(scope="session")
def ve_delegation(alice, VotingEscrowDelegation):
    return VotingEscrowDelegation.deploy({"from": alice})
