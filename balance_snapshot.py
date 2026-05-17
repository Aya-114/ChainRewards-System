from web3 import Web3
from solcx import compile_source, install_solc
import os
import csv

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

COIN_ADDRESS = addresses["COIN_ADDRESS"]

# ========== LOAD ABI ==========
install_solc("0.8.0")

with open("contracts/RewardPointCoin.sol", "r") as f:
    coin_source = f.read()
coin_abi = compile_source(coin_source, output_values=["abi"], solc_version="0.8.0")["<stdin>:RewardPointCoin"]["abi"]

coin = w3.eth.contract(address=COIN_ADDRESS, abi=coin_abi)

# ========== COLORS ==========
GREEN  = "\033[92m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# =====================================================
print(f"\n{CYAN}{BOLD}{'=' * 50}")
print("      BALANCE SNAPSHOT EXPORTER")
print(f"{'=' * 50}{RESET}")
print(f"  {YELLOW}Scanning blockchain for all accounts...{RESET}\n")

# ========== COLLECT ALL ADDRESSES FROM BLOCKCHAIN ==========
latest    = w3.eth.block_number
all_addrs = set()

for block_num in range(0, latest + 1):
    block = w3.eth.get_block(block_num, full_transactions=True)
    for tx in block.transactions:
        all_addrs.add(tx["from"])
        if tx["to"]:
            all_addrs.add(tx["to"])

# اضف الـ accounts اللى في Ganache كمان
for acc in w3.eth.accounts:
    all_addrs.add(acc)

# ========== BUILD SNAPSHOT ==========
snapshot = []

for addr in all_addrs:
    try:
        addr       = w3.to_checksum_address(addr)
        rpc_bal    = coin.functions.balanceOf(addr).call()
        eth_bal    = float(w3.from_wei(w3.eth.get_balance(addr), "ether"))
        snapshot.append({
            "Account Address":        addr,
            "Reward Point Coin Balance": rpc_bal,
            "ETH Balance":            round(eth_bal, 6)
        })
    except Exception:
        continue

# ========== PRINT TABLE ==========
print(f"  {'Address':<45} {'RPC':<8} {'ETH'}")
print("  " + "-" * 65)
for row in snapshot:
    print(f"  {row['Account Address']:<45} {row['Reward Point Coin Balance']:<8} {row['ETH Balance']:.4f} ETH")

# ========== SAVE CSV ==========
output_file = "balance_snapshot.csv"
with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "Account Address",
        "Reward Point Coin Balance",
        "ETH Balance"
    ])
    writer.writeheader()
    writer.writerows(snapshot)

print(f"\n  {GREEN}Snapshot saved to: {output_file}{RESET}")
print(f"  Total accounts: {len(snapshot)}")
print(f"{CYAN}{'=' * 50}{RESET}\n")
