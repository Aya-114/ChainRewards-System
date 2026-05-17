from web3 import Web3
from solcx import compile_source, install_solc
from collections import Counter
import os

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

# ========== LOAD ABI ==========
install_solc("0.8.0")

with open("contracts/StoreRewards.sol", "r", encoding="utf-8") as f:
    core_source = f.read()
core_abi = compile_source(core_source, output_values=["abi"], solc_version="0.8.0")["<stdin>:StoreRewards"]["abi"]

core = w3.eth.contract(address=CORE_ADDRESS, abi=core_abi)

# ========== COLORS ==========
GREEN  = "\033[92m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# =====================================================
print(f"\n{CYAN}{BOLD}{'=' * 50}")
print("      DATA HISTORY REPORT — REWARD POPULARITY")
print(f"{'=' * 50}{RESET}")
print(f"  {YELLOW}Scanning blockchain...{RESET}\n")

# ========== SCAN EVENTS ==========
latest         = w3.eth.block_number
purchase_count = Counter()   # reward_id -> count
purchase_costs = {}          # reward_id -> cost

for block_num in range(0, latest + 1):
    block = w3.eth.get_block(block_num, full_transactions=True)
    for tx in block.transactions:
        if tx["to"] and tx["to"].lower() == CORE_ADDRESS.lower():
            try:
                receipt = w3.eth.get_transaction_receipt(tx.hash)
                events  = core.events.RewardPurchased().process_receipt(receipt)
                for evt in events:
                    rid  = evt["args"]["id"]
                    cost = evt["args"]["cost"]
                    purchase_count[rid] += 1
                    purchase_costs[rid]  = cost
            except Exception:
                continue

# ========== GET REWARD NAMES ==========
reward_count = core.functions.rewardCount().call()
reward_names = {}
for i in range(1, reward_count + 1):
    try:
        r = core.functions.getReward(i).call()
        reward_names[i] = r[0]
    except:
        reward_names[i] = f"Reward #{i}"

# ========== PRINT TABLE ==========
print(f"  {'Rank':<6} {'Reward Name':<22} {'Cost':<8} {'Purchases':<10}")
print("  " + "-" * 50)

if not purchase_count:
    print("  No purchases found on the blockchain yet.")
else:
    ranked = sorted(purchase_count.items(), key=lambda x: x[1], reverse=True)
    for rank, (rid, count) in enumerate(ranked, 1):
        name = reward_names.get(rid, f"Reward #{rid}")
        cost = purchase_costs.get(rid, "?")
        bar  = "█" * count
        print(f"  {rank:<6} {name:<22} {str(cost)+' RPC':<8} {count:<5} {bar}")

# ========== REWARDS WITH ZERO PURCHASES ==========
zero = [reward_names[i] for i in range(1, reward_count + 1) if i not in purchase_count]
if zero:
    print(f"\n  {YELLOW}Not purchased yet:{RESET} {', '.join(zero)}")

total_purchases = sum(purchase_count.values())
print(f"\n  Total Purchases on Chain: {GREEN}{total_purchases}{RESET}")
print(f"{CYAN}{'=' * 50}{RESET}\n")
