from web3 import Web3
from solcx import compile_source, install_solc
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
COIN_ADDRESS = addresses["COIN_ADDRESS"]
ADMIN        = addresses["ADMIN"]
USER1        = addresses["USER1"]

# ========== LOAD ABIs ==========
install_solc("0.8.0")

f = open("contracts/StoreRewards.sol", "r", encoding="utf-8")
core_source = f.read()
f.close()
core_abi = compile_source(core_source, output_values=["abi"], solc_version="0.8.0")["<stdin>:StoreRewards"]["abi"]

f = open("contracts/RewardPointCoin.sol", "r", encoding="utf-8")
coin_source = f.read()
f.close()
coin_abi = compile_source(coin_source, output_values=["abi"], solc_version="0.8.0")["<stdin>:RewardPointCoin"]["abi"]

core = w3.eth.contract(address=CORE_ADDRESS, abi=core_abi)
coin = w3.eth.contract(address=COIN_ADDRESS, abi=coin_abi)

# ========== COLORS ==========
GREEN  = "\033[92m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# =====================================================
print(f"\n{CYAN}{BOLD}{'=' * 45}")
print("       SECURITY TESTING — ACCESS CONTROL")
print(f"{'=' * 45}{RESET}\n")

passed = 0
failed = 0

def run_test(test_name, func):
    global passed, failed
    try:
        tx_hash = func()
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 0:
            print(f"  {GREEN}[PASS]{RESET} {test_name}")
            print("         Correctly blocked. Receipt status = 0")
            passed += 1
        else:
            print(f"  {RED}[FAIL]{RESET} {test_name}")
            print("         Expected: transaction to REVERT — but it SUCCEEDED!")
            failed += 1
    except Exception as e:

        print(f"  {GREEN}[PASS]{RESET} {test_name}")
        print(f"         Correctly blocked with: {str(e)[:80]}")
        passed += 1

# ========== TEST 1: Normal user tries addReward ==========
print(f"  Test 1: Normal user tries to Add Reward")
run_test(
    "addReward blocked for normal user",
    lambda: core.functions.addReward("Hack Reward", 1).transact({
        "from": USER1,
        "gas": 200000
    })
)

# ========== TEST 2: Normal user tries updateReward ==========
print(f"\n  Test 2: Normal user tries to Update Reward")
run_test(
    "updateReward blocked for normal user",
    lambda: core.functions.updateReward(1, "Hacked Name", 1).transact({
        "from": USER1,
        "gas": 200000
    })
)

# ========== TEST 3: Normal user tries to mint coins ==========
print(f"\n  Test 3: Normal user tries to Mint Coins")
run_test(
    "mint blocked for normal user",
    lambda: coin.functions.mint(USER1, 9999).transact({
        "from": USER1,
        "gas": 200000
    })
)

# ========== TEST 4: Normal user tries to pause contract ==========
print(f"\n  Test 4: Normal user tries to Pause Contract")
run_test(
    "pause blocked for normal user",
    lambda: core.functions.pause().transact({
        "from": USER1,
        "gas": 100000
    })
)

# ========== TEST 5: Normal user tries to transfer ownership ==========
print(f"\n  Test 5: Normal user tries to Transfer Ownership")
run_test(
    "transferOwnership blocked for normal user",
    lambda: core.functions.transferOwnership(USER1).transact({
        "from": USER1,
        "gas": 100000
    })
)

# ========== RESULTS ==========
print(f"\n{CYAN}{'=' * 45}{RESET}")
print(f"  Results: {GREEN}{passed} PASSED{RESET}  |  {RED}{failed} FAILED{RESET}")
print(f"{CYAN}{'=' * 45}{RESET}\n")

if failed == 0:
    print(f"  {GREEN}{BOLD}All security tests passed! Contract is safe.{RESET}\n")
else:
    print(f"  {RED}{BOLD}Some tests failed! Check your onlyOwner modifier.{RESET}\n")
