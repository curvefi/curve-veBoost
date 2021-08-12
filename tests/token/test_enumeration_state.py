from collections import defaultdict
from functools import reduce

from brownie.network.account import Accounts
from brownie.network.contract import Contract
from brownie.test import strategy


class StateMachine:

    st_addr = strategy("address")

    def __init__(cls, accounts: Accounts, veboost: Contract):
        cls.alice = accounts[0]
        cls.accounts = accounts
        cls.veboost = veboost

    def setup(self):
        self.auto_id = 0
        self.total_supply = 0
        self.ownership = defaultdict(set)

    def rule_mint(self, st_addr):
        _id = self.auto_id
        self.veboost._mint_for_testing(st_addr, _id, {"from": st_addr})
        self.auto_id += 1

        self.ownership[st_addr].add(_id)
        self.total_supply += 1

    def rule_burn(self):
        if self.total_supply == 0:
            return

        token_id = reduce(lambda a, b: a | b, self.ownership.values(), set()).pop()
        _from = self.veboost.ownerOf(token_id)
        self.veboost._burn_for_testing(token_id, {"from": _from})

        self.ownership[_from].remove(token_id)
        self.total_supply -= 1

    def rule_transfer(self, st_addr):
        if self.total_supply == 0:
            return
        to = st_addr
        token_id = reduce(lambda a, b: a | b, self.ownership.values(), set()).pop()
        _from = self.veboost.ownerOf(token_id)

        self.veboost.transferFrom(_from, to, token_id, {"from": _from})

        self.ownership[_from].remove(token_id)
        self.ownership[to].add(token_id)

    def invariant_balanceOf(self):
        for acct in self.accounts:
            assert self.veboost.balanceOf(acct) == len(self.ownership[acct])

    def invariant_tokenOfOwnerByIndex(self):

        for acct in self.accounts:
            tokens = {
                self.veboost.tokenOfOwnerByIndex(acct, i) for i in range(len(self.ownership[acct]))
            }
            assert tokens == self.ownership[acct]

    def invariant_tokenByIndex(self):
        tokens = reduce(lambda a, b: a | b, self.ownership.values(), set())
        chain_tokens = {self.veboost.tokenByIndex(i) for i in range(len(tokens))}

        assert tokens == chain_tokens


def test_state_machine(state_machine, accounts, veboost):
    state_machine(StateMachine, accounts, veboost)
