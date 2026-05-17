from web3 import Web3
from solcx import compile_source, install_solc
import os
# ========== 1. CONNECT TO GANACHE ==========
w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))

if w3.is_connected():
    print("Connected to Ganache!")
else:
    print("Connection Failed!")
    exit()

# ========== 2. ACCOUNTS ==========
admin   = w3.eth.accounts[0]   # Admin
user1   = w3.eth.accounts[1]   # User 1
user2   = w3.eth.accounts[2]   # User 2

print(f" Admin  : {admin}")
print(f" User 1 : {user1}")
print(f" User 2 : {user2}")

# ========== 3. COMPILE CONTRACTS ==========
install_solc("0.8.0")

# --- Core Contract ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = SCRIPT_DIR
if not os.path.isdir(os.path.join(PROJECT_DIR, "contracts")):
    PROJECT_DIR = os.path.join(SCRIPT_DIR, "project Crypto")
os.chdir(PROJECT_DIR)
with open("contracts/StoreRewards.sol", "r") as f:
    with open("contracts/StoreRewards.sol", "r", encoding="utf-8") as f:
      core_source = f.read()

compiled_core = compile_source(
    core_source,
    output_values=["abi", "bin"],
    solc_version="0.8.0"
)
core_interface = compiled_core["<stdin>:StoreRewards"]
core_abi       = core_interface["abi"]
core_bytecode  = core_interface["bin"]

# --- Coin Contract ---
with open("contracts/RewardPointCoin.sol", "r", encoding="utf-8") as f:
    coin_source = f.read()

compiled_coin = compile_source(
    coin_source,
    output_values=["abi", "bin"],
    solc_version="0.8.0"
)
coin_interface = compiled_coin["<stdin>:RewardPointCoin"]
coin_abi       = coin_interface["abi"]
coin_bytecode  = coin_interface["bin"]

print("\nContracts Compiled!")

# ========== 4. DEPLOY CONTRACTS ==========

# Deploy Coin first
CoinContract = w3.eth.contract(
    abi=coin_abi,
    bytecode=coin_bytecode
)

coin_tx = CoinContract.constructor().transact({
    "from": admin,
    "gas": 3000000
})

coin_receipt = w3.eth.wait_for_transaction_receipt(coin_tx)
coin_address = coin_receipt.contractAddress

print("Coin deployed:", coin_address)


# Deploy Core AFTER coin
CoreContract = w3.eth.contract(
    abi=core_abi,
    bytecode=core_bytecode
)

core_tx = CoreContract.constructor(coin_address).transact({
    "from": admin,
    "gas": 3000000
})

core_receipt = w3.eth.wait_for_transaction_receipt(core_tx)
core_address = core_receipt.contractAddress

print("Core deployed:", core_address)

# ========== 5. CONNECT TO DEPLOYED CONTRACTS ==========
core = w3.eth.contract(address=core_address, abi=core_abi)
coin = w3.eth.contract(address=coin_address, abi=coin_abi)

link_tx = coin.functions.setStoreRewardsContract(core_address).transact({
    "from": admin,
    "gas": 100000
})
w3.eth.wait_for_transaction_receipt(link_tx)
print("Coin admin linked to Core admin")

# ========== 6. SEED FAKE REWARDS ==========
print("\n Adding fake rewards...")

rewards = [
    ("Free Coffee",   10),
    ("10% Discount",  25),
    ("Free Shipping", 15),
    ("Gift Card",     50),
    ("Free Sandwich", 30),
]

for name, cost in rewards:
    tx = core.functions.addReward(name, cost).transact({
        "from": admin,
        "gas": 200000
    })
    w3.eth.wait_for_transaction_receipt(tx)
    print(f"    Added: {name} to {cost} coins")

# ========== 7. MINT COINS FOR USERS ==========
print("\n Minting coins for users...")

coin.functions.mint(user1, 100).transact({"from": admin, "gas": 200000})
print(f"   Minted 100 coins to User1")

coin.functions.mint(user2, 50).transact({"from": admin, "gas": 200000})
print(f"   Minted 50 coins  to User2")

# ========== 8. VERIFY SETUP ==========
print("\n Verifying Setup...")

reward_count = core.functions.rewardCount().call()
print(f"    Total Rewards : {reward_count}")

user1_balance = coin.functions.balanceOf(user1).call()
user2_balance = coin.functions.balanceOf(user2).call()

print(f"User1 Balance : {user1_balance} RPC")
print(f"User2 Balance : {user2_balance} RPC")

total_supply = coin.functions.totalSupply().call()
print(f"    Total Supply  : {total_supply} RPC")

# ========== 9. SAVE ADDRESSES ==========
with open("contract_addresses.txt", "w") as f:
    f.write(f"CORE_ADDRESS={core_address}\n")
    f.write(f"COIN_ADDRESS={coin_address}\n")
    f.write(f"ADMIN={admin}\n")
    f.write(f"USER1={user1}\n")
    f.write(f"USER2={user2}\n")

print("\n Addresses saved to contract_addresses.txt")
print("\n Setup Complete! Ready to run the app.")



