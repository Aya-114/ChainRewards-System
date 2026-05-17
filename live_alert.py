from web3 import Web3
from solcx import compile_source, install_solc
import os
import time

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

# ========== LOAD ABI ==========
install_solc("0.8.0")

with open("contracts/StoreRewards.sol", "r", encoding="utf-8") as f:
    core_source = f.read()
core_abi = compile_source(core_source, output_values=["abi"], solc_version="0.8.0")["<stdin>:StoreRewards"]["abi"]

core = w3.eth.contract(address=CORE_ADDRESS, abi=core_abi)

# ========== COLORS ==========
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# =====================================================
print(f"\n{CYAN}{BOLD}{'=' * 45}")
print("    LIVE ALERT SYSTEM — REWARD MONITOR")
print(f"{'=' * 45}{RESET}")
print(f"  {YELLOW}Watching for new transactions...{RESET}")
print(f"  Press Ctrl+C to stop.\n")

last_block = w3.eth.block_number

while True:
    try:
        current_block = w3.eth.block_number

        if current_block > last_block:
            for block_num in range(last_block + 1, current_block + 1):
                block = w3.eth.get_block(block_num, full_transactions=True)

                for tx in block.transactions:
                    if tx["to"] and tx["to"].lower() == CORE_ADDRESS.lower():

                        # حاول تفك الـ event من الـ receipt
                        try:
                            receipt = w3.eth.get_transaction_receipt(tx.hash)
                            events  = core.events.RewardPurchased().process_receipt(receipt)

                            if events:
                                for evt in events:
                                    user    = evt["args"]["user"]
                                    reward_id = evt["args"]["id"]
                                    cost    = evt["args"]["cost"]
                                    print(f"  {RED}{BOLD}🚨 ALERT: A reward purchase just happened!{RESET}")
                                    print(f"     User     : {user}")
                                    print(f"     Reward ID: {reward_id}")
                                    print(f"     Cost     : {cost} RPC")
                                    print(f"     Block    : {block_num}")
                                    print(f"     TX Hash  : {tx.hash.hex()}\n")
                            else:
                                # transaction على الـ contract بس مش reward purchase
                                print(f"  {YELLOW}[Block {block_num}]{RESET} Contract interaction detected — TX: {tx.hash.hex()[:20]}...")

                        except Exception:
                            # لو مش قدرنا نفك الـ event، طبع تحذير عام
                            print(f"  {YELLOW}[Block {block_num}]{RESET} New transaction on contract detected.")

            last_block = current_block

        time.sleep(2)  # انتظر ثانيتين وبعدين اشيك تاني

    except KeyboardInterrupt:
        print(f"\n{CYAN}  Alert system stopped.{RESET}\n")
        break
    except Exception as e:
        print(f"{RED}  Error: {e}{RESET}")
        time.sleep(2)
