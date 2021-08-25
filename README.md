# Curve Voting Escrow Boost Delegation

The Curve DAO Token is the utility token of the Curve Finance ecosystem, primarily created to incentivise liquidity providers on the platform.
However, when staked the CRV token becomes veCRV, a non-transferable, linearly decaying, governance token with 2 special abilities. The first
is holders of veCRV receive boosted rewards on provided liquidity (up to a maximum of 2.5x), and the second is holders receive 50% of all the
trading fees collected across all Curve Finance pools (including factory pools + altchains) in the form of 3CRV.

With the release of the Curve veBoost, veCRV holders can now delegate a fixed allotment of their veCRV boost to third-party accounts in the form of
an NFT. These veBoost tokens, are wrapped packages of boost which eligible gauges (currently only factory gauges) use to determine boosted rewards
on provided liquidity. This means any account can receive boosted rewards on provided liquidity, without holding veCRV.

For eligible gauges, the equation for determining your adjusted veCRV balance is:

`Adjusted veCRV Balance = veCRV Balance - delegated veBoost + received veBoost`

Restrictions:

- Minimum delegation period is `1 Week`
- Maximum delegation period is the delegator's veCRV lock end
- Delegators can't delegate more than their `veCRV balance - any outstanding veBoosts`
- Delegators can't newly delegate (or extend a delegation) with any outstanding negative veBoosts
- Delegators can't cancel a veBoost before it's cancel time
- Receivers can cancel a received veBoost at any time
- Third parties can't cancel a veboost unless it is expired
- Delegated boost is internally equal to, `abs(sum(delegated veboost))`, meaning an accounts veCRV balance can never get
  inflated due to negative outstanding boosts
- Received boost is internally equal to, `max(received veboost, 0)`, meaning an accounts received boost balance will never
  result in decreasing their vanilla veCRV balance

The adjusted formula on chain therefore is:

`Adjusted veCRV Balance = veCRV Balance - abs(delegated veBoost) + max(received veBoost, 0)`

In fact, if an account does not participate in delegating veBoost, their adjusted veCRV balance will never be below their vanilla veCRV balance.


### Deployments


- [VotingEscrowDelegation.vy](contracts/VotingEscrowDelegation.vy): [0xc620aaFD6Caa3Cb7566e54176dD2ED1A81d05655](https://etherscan.io/address/0xc620aaFD6Caa3Cb7566e54176dD2ED1A81d05655)
- [DelegationProxy.vy](contracts/DelegationProxy.vy): [0x8E0c00ed546602fD9927DF742bbAbF726D5B0d16](https://etherscan.io/address/0x8E0c00ed546602fD9927DF742bbAbF726D5B0d16)


### Dependencies

* [python3](https://www.python.org/downloads/release/python-368/) version 3.6 or greater, python3-dev
* [brownie](https://github.com/eth-brownie/brownie) - tested with version [1.15.0](https://github.com/eth-brownie/brownie/releases/tag/v1.15.0)
* [brownie-token-tester](https://github.com/iamdefinitelyahuman/brownie-token-tester)
* [ganache-cli](https://github.com/trufflesuite/ganache-cli) - tested with version [6.12.1](https://github.com/trufflesuite/ganache-cli/releases/tag/v6.12.1)

Also check the [requirements.txt](./requirements.txt)

### Testing

Testing is performed in a local development environment

To run the unit tests:

```bash
brownie test --stateful false
```

To run the state tests:

```bash
brownie test --stateful true
```

### Deployment

To deploy the contracts, first modify the [`deployment script`](scripts/deploy.py) to unlock the account you wish to deploy from. Then:

```bash
brownie run deploy --network mainnet
```

### License

(c) Curve.Fi, 2021 - [All rights reserved](LICENSE).
