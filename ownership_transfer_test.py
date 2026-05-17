from web3 import Web3
from solcx import compile_source, install_solc
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = SCRIPT_DIR
if not os.path.isdir(os.path.join(PROJECT_DIR, "contracts")):
    PROJECT_DIR = os.path.join(SCRIPT_DIR, "project Crypto")
os.chdir(PROJECT_DIR)

w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))
if not w3.is_connected():
    print("Connection Failed!")
    exit()

addresses = {}
with open("contract_addresses.txt", "r") as f:
    for line in f:
        key, value = line.strip().split("=")
        addresses[key] = value

CORE_ADDRESS = addresses["CORE_ADDRESS"]
COIN_ADDRESS = addresses["COIN_ADDRESS"]
ORIGINAL_ADMIN = w3.eth.accounts[0]
NEW_ADMIN = w3.eth.accounts[2]

install_solc("0.8.0")

with open("contracts/StoreRewards.sol", "r", encoding="utf-8") as f:
    core_source = f.read()

with open("contracts/RewardPointCoin.sol", "r", encoding="utf-8") as f:
    coin_source = f.read()

core_abi = compile_source(
    core_source,
    output_values=["abi"],
    solc_version="0.8.0"
)["<stdin>:StoreRewards"]["abi"]

coin_abi = compile_source(
    coin_source,
    output_values=["abi"],
    solc_version="0.8.0"
)["<stdin>:RewardPointCoin"]["abi"]

core = w3.eth.contract(address=CORE_ADDRESS, abi=core_abi)
coin = w3.eth.contract(address=COIN_ADDRESS, abi=coin_abi)

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_result(ok, label, details=""):
    status = f"{GREEN}[PASS]{RESET}" if ok else f"{RED}[FAIL]{RESET}"
    print(f"  {status} {label}")
    if details:
        print(f"         {details}")


def send_and_check(label, tx_builder, sender, expect_success):
    try:
        tx_hash = tx_builder().transact({"from": sender, "gas": 300000})
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        success = receipt.status == 1
        ok = success == expect_success
        print_result(ok, label, f"tx={receipt.transactionHash.hex()} status={receipt.status}")
        return ok
    except Exception as e:
        success = False
        ok = success == expect_success
        print_result(ok, label, f"blocked with: {str(e)[:90]}")
        return ok


print(f"\n{CYAN}{BOLD}{'=' * 55}")
print("       OWNERSHIP TRANSFER TEST")
print(f"{'=' * 55}{RESET}\n")

current_admin = core.functions.getAdmin().call()
coin_admin = coin.functions.getAdmin().call()
print(f"  Current Admin : {current_admin}")
print(f"  Coin Admin    : {coin_admin}")
print(f"  Account 1     : {ORIGINAL_ADMIN}")
print(f"  Account 3     : {NEW_ADMIN}\n")

if current_admin.lower() != ORIGINAL_ADMIN.lower():
    print(f"{RED}  Stop: Account 1 must be the admin before this test starts.{RESET}")
    print(f"{YELLOW}  Run setup.py again or transfer ownership back to Account 1 first.{RESET}\n")
    exit()

if core.functions.paused().call():
    print(f"{YELLOW}  Contract is paused. Resuming before test...{RESET}")
    tx = core.functions.resume().transact({"from": ORIGINAL_ADMIN, "gas": 100000})
    w3.eth.wait_for_transaction_receipt(tx)

passed = 0
total = 7

if send_and_check(
    "1. Original admin can add a reward before transfer",
    lambda: core.functions.addReward("Ownership Test Original", 1),
    ORIGINAL_ADMIN,
    True
):
    passed += 1

if send_and_check(
    "2. Original admin can mint coins before transfer",
    lambda: coin.functions.mint(NEW_ADMIN, 1),
    ORIGINAL_ADMIN,
    True
):
    passed += 1

if send_and_check(
    "3. Original admin transfers ownership to Account 3",
    lambda: core.functions.transferOwnership(NEW_ADMIN),
    ORIGINAL_ADMIN,
    True
):
    passed += 1

if send_and_check(
    "4. Original admin is blocked from core actions after transfer",
    lambda: core.functions.addReward("Should Fail Original", 1),
    ORIGINAL_ADMIN,
    False
):
    passed += 1

if send_and_check(
    "5. Original admin is blocked from minting after transfer",
    lambda: coin.functions.mint(ORIGINAL_ADMIN, 1),
    ORIGINAL_ADMIN,
    False
):
    passed += 1

if send_and_check(
    "6. New admin can add a reward after transfer",
    lambda: core.functions.addReward("Ownership Test New Admin", 2),
    NEW_ADMIN,
    True
):
    passed += 1

if send_and_check(
    "7. New admin can mint coins after transfer",
    lambda: coin.functions.mint(NEW_ADMIN, 1),
    NEW_ADMIN,
    True
):
    passed += 1

current_admin = core.functions.getAdmin().call()
if current_admin.lower() == NEW_ADMIN.lower():
    print(f"\n{YELLOW}  Restoring ownership back to Account 1 for normal app testing...{RESET}")
    tx = core.functions.transferOwnership(ORIGINAL_ADMIN).transact({"from": NEW_ADMIN, "gas": 100000})
    receipt = w3.eth.wait_for_transaction_receipt(tx)
    print(f"  Restore tx: {receipt.transactionHash.hex()} status={receipt.status}")

final_admin = core.functions.getAdmin().call()
print(f"\n  Final Admin: {final_admin}")
print(f"{CYAN}{'=' * 55}{RESET}")
print(f"  Results: {GREEN}{passed} PASSED{RESET} / {total}")
print(f"{CYAN}{'=' * 55}{RESET}\n")
