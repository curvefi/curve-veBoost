from collections import defaultdict
from functools import reduce

from brownie import ZERO_ADDRESS
from brownie.network.account import Accounts
from brownie.network.contract import Contract
from brownie.test import strategy


class StateMachine:

    st_addr = strategy("address")
    st_id = strategy("uint96")

    def __init__(cls, accounts: Accounts, veboost: Contract):
        cls.alice = accounts[0]
        cls.accounts = accounts
        cls.veboost = veboost

    def setup(self):
        self.total_supply = 0
        self.ownership = defaultdict(set)

    def rule_mint(self, st_addr, st_id):
        token_id = self.veboost.get_token_id(st_addr, st_id)
        if self.veboost.ownerOf(token_id) != ZERO_ADDRESS:
            return
        self.veboost._mint_for_testing(st_addr, token_id, {"from": st_addr})

        self.ownership[st_addr].add(token_id)
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
    state_machine(StateMachine, accounts, veboost, settings={"stateful_step_count": 50})
