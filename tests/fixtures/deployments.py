import brownie
import pytest
from brownie import compile_source


@pytest.fixture(scope="session")
def crv(alice, pm):
    ERC20CRV = pm("curvefi/curve-dao-contracts@1.1.0").ERC20CRV
    return ERC20CRV.deploy("Curve DAO Token", "CRV", 18, {"from": alice})


@pytest.fixture(scope="session")
def vecrv(alice, crv, pm):
    VotingEscrow = pm("curvefi/curve-dao-contracts@1.1.0").VotingEscrow
    return VotingEscrow.deploy(crv, "Vote-Escrowed CRV", "veCRV", "Version 1.0.0", {"from": alice})


@pytest.fixture(scope="session")
def veboost(alice, VotingEscrowDelegation, vecrv):
    source = VotingEscrowDelegation._build["source"]
    source = source.replace("0x19854C9A5fFa8116f48f984bDF946fB9CEa9B5f7", vecrv.address)

    NewVotingEscrowDelegation = compile_source(source).Vyper
    return NewVotingEscrowDelegation.deploy(
        "Curve veCRV Boost", "veCRV-Boost", "", alice, {"from": alice}
    )


@pytest.fixture(scope="session", autouse=True)
def multicall(alice):
    return brownie.multicall.deploy({"from": alice})
