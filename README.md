# Store Rewards & Points

This project is a blockchain app for a store reward system. Users can register, check rewards, spend Reward Point Coin, and view account history. The admin can manage rewards, mint coins, pause the system, and transfer ownership. The project includes both the original terminal app and a real desktop GUI.

## Requirements

- Ganache running on `HTTP://127.0.0.1:7545`
- Python
- Python packages: `web3` and `py-solc-x`

## Setup

1. Open Ganache.
2. Start a workspace or Quickstart chain.
3. Confirm the RPC server is `HTTP://127.0.0.1:7545`.
4. Open PowerShell in this folder.
5. Run:

```powershell
python setup.py
```

The setup script deploys the Reward Point Coin contract, deploys the Store Rewards contract, adds sample rewards, mints sample coins, and saves the contract addresses in `contract_addresses.txt`.

## Setup With Truffle

The project is also connected to Truffle. Keep Ganache running on port `7545`, then run:

```powershell
truffle compile
truffle migrate --network development --reset
```

If Ganache shows interface entries like `IRewardPointCoin` or `StoreRewardsAdmin` as `Not Deployed`, that is normal because interfaces are not deployable contracts. To hide those interface artifacts from Ganache after migrating, run:

```powershell
node scripts\clean_truffle_interfaces.js
```

Or use the combined npm script:

```powershell
npm run migrate:clean
```

The Truffle migration deploys the same contracts, links the coin admin to the core admin, adds the fake rewards, mints sample RPC to User 1 and User 2, and writes fresh addresses to:

```text
project Crypto\contract_addresses.txt
```

After Truffle migration, you can run the same apps:

```powershell
python gui_app.py
python app.py
```

## Run The Terminal App

```powershell
python app.py
```

Choose an account number from the list. First-time users must enter a name to register on-chain.

## Run The Real GUI

After Ganache is open and `python setup.py` has finished successfully, run:

```powershell
python gui_app.py
```

The GUI opens a desktop window with four tabs:

- User: register a wallet name, view rewards, buy rewards, check balances, transfer coins, and scan address history.
- Admin: unlock with password `crypto2024`, then add/update rewards, batch add/update rewards, mint coins, pause/resume the contract, and transfer ownership.
- System: view contract addresses, admin addresses, Ganache balances, total rewards, total minted coins, contract transaction count, top 3 active users, popular rewards, and export `balance_snapshot.csv`.
- Log: start/stop live purchase alerts. When a reward is bought, the log prints `ALERT: A reward purchase just happened!`.

## Normal User Actions

From the main menu, a normal user can:

- View all available rewards.
- Buy a reward using Reward Point Coin.
- Check their own coin and ETH balance.
- Transfer coins to another address.
- View one reward by ID.
- Check any address balance.
- View activity history for any address.

## Admin Actions

Use Account 1 as the admin account after running `setup.py`.

From the main menu, type:

```text
admin
```

Then enter the admin password:

```text
crypto2024
```

The admin can:

- Add one reward.
- Update one reward.
- Batch add several rewards.
- Batch update several rewards.
- Give coins to users.
- View rewards.
- Check balances.
- View activity history.
- Pause the contract.
- Resume the contract.
- Transfer ownership.

## Background And Test Scripts

Run these scripts from this folder:

```powershell
python Admin_dashboard.py
python history_report.py
python balance_snapshot.py
python security_test.py
python ownership_transfer_test.py
```

To test live alerts, open two PowerShell windows.

In the first one, run:

```powershell
python live_alert.py
```

In the second one, run:

```powershell
python app.py
```

Buy a reward from the app. The live alert window should print an alert for the reward purchase.

## Important Notes

- If Ganache is restarted or reset, run `python setup.py` again.
- If the app shows `0 ETH` for an old address, copy a fresh address from the current Ganache account list.
- Keep ownership on Account 1 for easy admin testing.
- `Pause` blocks reward actions and new user registration until `Resume` is used.
- The Reward Point Coin admin is linked to the Core contract admin during setup, so `transferOwnership` moves both reward-management and coin-minting authority to the new admin.
