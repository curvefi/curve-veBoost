from ape import accounts, project

primary = accounts.load("primary")


def main():
    project.BoostV2.deploy(
        "0xd30DD0B919cB4012b3AdD78f6Dcb6eb7ef225Ac8",
        "0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2",
        sender=primary,
    )
