import pytest
from brownie import ZERO_ADDRESS


@pytest.fixture(scope="session")
def ve_delegation(alice, VotingEscrowDelegation):
    return VotingEscrowDelegation.deploy(
        "Curve veCRV Boost", "veCRV-Boost", ZERO_ADDRESS, {"from": alice}
    )
