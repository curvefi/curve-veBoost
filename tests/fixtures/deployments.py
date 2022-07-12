import pytest


@pytest.fixture(scope="session")
def crv(alice, project):
    yield project.dependencies["curve-dao"]["1.3.0"].ERC20CRV.deploy(
        "Curve DAO Token", "CRV", 18, sender=alice
    )


@pytest.fixture(scope="session")
def ve(alice, crv, project):
    yield project.dependencies["curve-dao"]["1.3.0"].VotingEscrow.deploy(
        crv, "Vote-Escrowed CRV", "veCRV", "1.0.0", sender=alice
    )


@pytest.fixture(scope="session")
def veboost_v1(alice, project, ve):
    yield project.VotingEscrowDelegation.deploy(
        "Vote-Escrowed Boost", "veBoost", "", ve, sender=alice
    )


@pytest.fixture(scope="session")
def veboost(alice, project, ve, veboost_v1):
    yield project.BoostV2.deploy(veboost_v1, ve, sender=alice)
