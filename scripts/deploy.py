from brownie import VotingEscrowDelegation, VotingEscrowWrapper, accounts


def main():
    DEPLOYER = accounts.load("veOracle-deployer")

    VotingEscrowDelegation.deploy(
        "Voting Escrow Boost Delegation",
        "veBoost",
        "",
        {"from": DEPLOYER},
    )
    VotingEscrowWrapper.deploy({"from": DEPLOYER})

