import pytest

DAY = 86400
WEEK = DAY * 7


@pytest.fixture(scope="session")
def ZERO_ADDRESS():
    yield "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[2]


@pytest.fixture(scope="module")
def crv(alice, project):
    yield project.dependencies["curve-dao"]["1.3.0"].ERC20CRV.deploy(
        "Curve DAO Token", "CRV", 18, sender=alice
    )


@pytest.fixture(scope="module")
def ve(alice, crv, project):
    yield project.dependencies["curve-dao"]["1.3.0"].VotingEscrow.deploy(
        crv, "Vote-Escrowed CRV", "veCRV", "1.0.0", sender=alice
    )


@pytest.fixture(scope="module")
def veboost_v1(alice, project, ve):
    yield project.VotingEscrowDelegation.deploy(
        "Vote-Escrowed Boost", "veBoost", "", ve, sender=alice
    )


@pytest.fixture(scope="module")
def veboost(alice, project, ve, veboost_v1):
    yield project.BoostV2.deploy(veboost_v1, ve, sender=alice)
