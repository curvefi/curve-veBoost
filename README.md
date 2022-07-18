# CurveFi Vote-Escrowed Boost

veBoost is an non-transferrable token representing boost in the CurveFi gauge system. veCRV holders can boost any address of their choice, enabling the aggregation of
boosted reward power at a single address. For example, enabling smart contracts to earn boosted CRV emissions, without giving up DAO voting rights, or weekly 3CRV fee allocations.

### Deployments


- [BoostV2.vy](contracts/BoostV2.vy): [0xD0921691C7DEBc698e6e372c6f74dc01fc9d3778](https://etherscan.io/address/0xD0921691C7DEBc698e6e372c6f74dc01fc9d3778)
- [DelegationProxy.vy](contracts/DelegationProxy.vy): [0x8E0c00ed546602fD9927DF742bbAbF726D5B0d16](https://etherscan.io/address/0x8E0c00ed546602fD9927DF742bbAbF726D5B0d16)


### Dependencies

* [python3](https://www.python.org/downloads/release/python-368/) version 3.6 or greater, python3-dev
- [eth-ape](https://github.com/ApeWorX/ape)

Also check the [requirements.txt](./requirements.txt)

### Testing

Testing is performed in a local development environment

To run the unit tests:

```bash
npm ci
ape test
```

### Deployment

To deploy the contracts, first modify the [`deployment script`](scripts/deploy.py) to unlock the account you wish to deploy from. Then:

```bash
ape run deploy
```

### License

(c) Curve.Fi, 2021 - [All rights reserved](LICENSE).
