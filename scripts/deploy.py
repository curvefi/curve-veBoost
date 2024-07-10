from ape import accounts, project, Contract

primary = accounts.load("primary")


def main():
    project.BoostV2.deploy(
        "0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2",
        sender=primary,
    )