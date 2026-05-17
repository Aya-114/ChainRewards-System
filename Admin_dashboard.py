from web3 import Web3
from solcx import compile_source, install_solc
import os
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = SCRIPT_DIR
if not os.path.isdir(os.path.join(PROJECT_DIR, "contracts")):
    PROJECT_DIR = os.path.join(SCRIPT_DIR, "project Crypto")
os.chdir(PROJECT_DIR)

# ========== CONNECT ==========
w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))
if not w3.is_connected():
    print("Connection Failed!")
    exit()

# ========== LOAD ADDRESSES ==========
addresses = {}
with open("contract_addresses.txt", "r") as f:
    for line in f:
        key, value = line.strip().split("=")
        addresses[key] = value

CORE_ADDRESS = addresses["CORE_ADDRESS"]
COIN_ADDRESS = addresses["COIN_ADDRESS"]
ADMIN        = addresses["ADMIN"]

# ========== LOAD ABIs ==========
install_solc("0.8.0")

with open("contracts/StoreRewards.sol", "r", encoding="utf-8") as f:
    core_source = f.read()
core_abi = compile_source(core_source, output_values=["abi"], solc_version="0.8.0")["<stdin>:StoreRewards"]["abi"]

with open("contracts/RewardPointCoin.sol", "r", encoding="utf-8") as f:
    coin_source = f.read()
coin_abi = compile_source(coin_source, output_values=["abi"], solc_version="0.8.0")["<stdin>:RewardPointCoin"]["abi"]

core = w3.eth.contract(address=CORE_ADDRESS, abi=core_abi)
coin = w3.eth.contract(address=COIN_ADDRESS, abi=coin_abi)

# ========== COLORS ==========
GREEN  = "\033[92m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# =====================================================
print(f"\n{CYAN}{BOLD}{'=' * 45}")
print("       ADMIN DASHBOARD — SYSTEM SUMMARY")
print(f"{'=' * 45}{RESET}\n")

# ========== 1. TOTAL REWARDS ==========
reward_count = core.functions.rewardCount().call()
print(f"{YELLOW}  1. Total Rewards in Contract:{RESET} {reward_count}")

# ========== 2. TOTAL COINS MINTED ==========
total_supply = coin.functions.totalSupply().call()
print(f"{YELLOW}  2. Total Coins Minted (RPC):{RESET}  {total_supply}")

# ========== 3. SCAN BLOCKCHAIN ==========
print("Scanning blockchain...")

latest = w3.eth.block_number
print("Latest block:", latest)

tx_count = 0
sender_counts = Counter()

for block_num in range(0, latest + 1):
    print(f"Block {block_num}/{latest}")

    block = w3.eth.get_block(block_num, full_transactions=True)

    for tx in block.transactions:
        if tx["to"] is None:
            continue

        if tx["to"].lower() in [CORE_ADDRESS.lower(), COIN_ADDRESS.lower()]:
            tx_count += 1
            sender_counts[tx["from"]] += 1
# ========== 4. TOTAL TRANSACTIONS ==========
print(f"{YELLOW}  3. Total Transactions on Contracts:{RESET} {tx_count}")

# ========== 5. TOP 3 ACTIVE USERS ==========
print(f"\n{YELLOW}  4. Top 3 Most Active Addresses:{RESET}")
print(f"  {'Address':<45} {'Transactions'}")
print("  " + "-" * 55)

if sender_counts:
    top3 = sender_counts.most_common(3)
    for i, (addr, count) in enumerate(top3, 1):
        label = " (Admin)" if addr.lower() == ADMIN.lower() else ""
        print(f"  {i}. {addr}{label} — {count} tx")
else:
    print("  No transactions found yet.")

print(f"\n{CYAN}{'=' * 45}{RESET}\n")
