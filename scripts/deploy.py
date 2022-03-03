from brownie import VotingEscrowDelegation, accounts


def main():
    DEPLOYER = accounts.load("veOracle-deployer")
    VotingEscrowDelegation.deploy(
        "Voting Escrow Boost Delegation",
        "veBoost",
        "",
        {"from": DEPLOYER},
    )
    with open("etherscan_source_verification.vy", "w") as f:
        # we use jinja in the file, but the deployed source will
        # not have any testing code blocks
        # can verify by trying in mainnet-fork
        # brownie run deploy --network mainnet-fork -I
        # and checking the sauce
        sauce = VotingEscrowDelegation._build["source"]
        f.write(sauce)
