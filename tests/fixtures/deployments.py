import pytest


@pytest.fixture(scope="session")
def ve_delegation(alice, VotingEscrowDelegation):
    return VotingEscrowDelegation.deploy("Curve veCRV Boost", "veCRV-Boost", {"from": alice})
