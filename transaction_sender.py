from web3 import Web3
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = SCRIPT_DIR
if not os.path.isdir(os.path.join(PROJECT_DIR, "contracts")):
    PROJECT_DIR = os.path.join(SCRIPT_DIR, "project Crypto")
os.chdir(PROJECT_DIR)

# ========== 1. CONNECT TO GANACHE ==========
w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))

if not w3.is_connected():
    print("Connection Failed!")
    exit()

# ========== 2. LOAD ADDRESSES ==========
addresses = {}
with open("contract_addresses.txt", "r") as f:
    for line in f:
        key, value = line.strip().split("=")
        addresses[key] = value

CORE_ADDRESS = addresses["CORE_ADDRESS"]
COIN_ADDRESS = addresses["COIN_ADDRESS"]
ADMIN = w3.eth.accounts[0]

# ========== 3. LOAD ABIs ==========
from solcx import compile_source, install_solc
install_solc("0.8.0")

with open("contracts/StoreRewards.sol", "r", encoding="utf-8") as f:
    core_source = f.read()
compiled_core = compile_source(core_source,
                               output_values=["abi"],
                               solc_version="0.8.0")
core_abi = compiled_core["<stdin>:StoreRewards"]["abi"]

with open("contracts/RewardPointCoin.sol", "r", encoding="utf-8") as f:
    coin_source = f.read()
compiled_coin = compile_source(coin_source,
                               output_values=["abi"],
                               solc_version="0.8.0")
coin_abi = compiled_coin["<stdin>:RewardPointCoin"]["abi"]

# ========== 4. CONNECT TO CONTRACTS ==========
core = w3.eth.contract(address=CORE_ADDRESS, abi=core_abi)
coin = w3.eth.contract(address=COIN_ADDRESS, abi=coin_abi)

print("Connected to contracts!")

# =====================================================
# ========== ADMIN FUNCTIONS ==========
# =====================================================

def admin_add_reward(name, cost, sender=ADMIN):
    try:
        tx      = core.functions.addReward(name, cost).transact({"from": sender, "gas": 200000})
        receipt = w3.eth.wait_for_transaction_receipt(tx)
        print(f"Reward added: {name} for {cost} coins")
        print(f"TX Hash : {receipt.transactionHash.hex()}")
        return True
    except Exception as e:
        print(f"Failed to add reward: {e}")
        return False

def admin_update_reward(reward_id, new_name, new_cost, sender=ADMIN):
    try:
        tx      = core.functions.updateReward(reward_id, new_name, new_cost).transact({"from": sender, "gas": 200000})
        receipt = w3.eth.wait_for_transaction_receipt(tx)
        print(f"Reward {reward_id} updated to {new_name} / {new_cost} coins")
        print(f"TX Hash : {receipt.transactionHash.hex()}")
        return True
    except Exception as e:
        print(f"Failed to update reward: {e}")
        return False

def admin_batch_add(names, costs, sender=ADMIN):
    try:
        tx      = core.functions.batchAddRewards(names, costs).transact({"from": sender, "gas": 500000})
        receipt = w3.eth.wait_for_transaction_receipt(tx)
        print(f"Batch added {len(names)} rewards!")
        print(f"TX Hash : {receipt.transactionHash.hex()}")
        return True
    except Exception as e:
        print(f"Batch add failed: {e}")
        return False

def admin_batch_update(ids, names, costs, sender=ADMIN):
    try:
        tx      = core.functions.batchUpdateRewards(ids, names, costs).transact({"from": sender, "gas": 500000})
        receipt = w3.eth.wait_for_transaction_receipt(tx)
        print(f"Batch updated {len(ids)} rewards!")
        print(f"TX Hash : {receipt.transactionHash.hex()}")
        return True
    except Exception as e:
        print(f"Batch update failed: {e}")
        return False

def admin_mint_coins(to_address, amount, sender=ADMIN):
    try:
        to_address = w3.to_checksum_address(to_address)
        tx         = coin.functions.mint(to_address, int(amount)).transact({"from": sender, "gas": 300000})
        receipt    = w3.eth.wait_for_transaction_receipt(tx)
        print(f"Minted {amount} RPC to {to_address}")
        print(f"TX Hash : {receipt.transactionHash.hex()}")
        return True
    except Exception as e:
        print(f"Mint failed: {e}")
        return False

def admin_give_coins(to_address, amount, sender=ADMIN):
    return admin_mint_coins(to_address, amount, sender)

def admin_pause(sender=ADMIN):
    try:
        tx = core.functions.pause().transact({"from": sender, "gas": 100000})
        w3.eth.wait_for_transaction_receipt(tx)
        print("Contract PAUSED!")
        return True
    except Exception as e:
        print(f"Pause failed: {e}")
        return False

def admin_resume(sender=ADMIN):
    try:
        tx = core.functions.resume().transact({"from": sender, "gas": 100000})
        w3.eth.wait_for_transaction_receipt(tx)
        print("Contract RESUMED!")
        return True
    except Exception as e:
        print(f"Resume failed: {e}")
        return False

def admin_transfer_ownership(new_admin, sender=ADMIN):
    try:
        new_admin = w3.to_checksum_address(new_admin)
        tx        = core.functions.transferOwnership(new_admin).transact({"from": sender, "gas": 100000})
        receipt   = w3.eth.wait_for_transaction_receipt(tx)
        print(f"Core and coin admin rights transferred to {new_admin}")
        print(f"TX Hash: {receipt.transactionHash.hex()}")
        return True
    except Exception as e:
        print(f"Transfer failed: {e}")
        return False

# =====================================================
# ========== USER FUNCTIONS ==========
# =====================================================

# -------- Register User --------
def user_register(name, sender):
    try:
        tx      = core.functions.registerUser(name).transact({"from": sender, "gas": 200000})
        receipt = w3.eth.wait_for_transaction_receipt(tx)
        print(f"Registered as: {name}")
        print(f"TX Hash : {receipt.transactionHash.hex()}")
        return True
    except Exception as e:
        print(f"Registration failed: {e}")
        return False

# -------- Get User Name --------
def get_user_name(address):
    try:
        return core.functions.getUserName(address).call()
    except:
        return ""

# -------- Check If Registered --------
def is_registered(address):
    try:
        return core.functions.isRegistered(address).call()
    except:
        return False

# -------- Buy Reward --------
# الخطوات: 1) approve  2) buyReward
def user_buy_reward(reward_id, sender):
    try:
        reward     = core.functions.getReward(reward_id).call()
        name, cost = reward[0], reward[1]

        balance = coin.functions.balanceOf(sender).call()
        if balance < cost:
            print("Not enough coins!")
            print(f"Your balance : {balance} RPC")
            print(f"Reward costs : {cost} RPC")
            return False

        # Step 1: approve — الـ user بيسمح للـ core contract يسحب الكوين
        approve_tx = coin.functions.approve(CORE_ADDRESS, cost).transact({
            "from": sender,
            "gas": 100000
        })
        w3.eth.wait_for_transaction_receipt(approve_tx)

        # Step 2: buyReward — الـ contract تسحب وتسجل العملية
        buy_tx  = core.functions.buyReward(reward_id).transact({
            "from": sender,
            "gas": 200000
        })
        receipt = w3.eth.wait_for_transaction_receipt(buy_tx)

        print(f"Bought: {name} for {cost} coins!")
        print(f"TX Hash : {receipt.transactionHash.hex()}")
        return True

    except Exception as e:
        print(f"Buy failed: {e}")
        return False

# -------- Transfer Coins --------
def user_transfer_coins(to_address, amount, sender):
    try:
        balance = coin.functions.balanceOf(sender).call()
        if balance < amount:
            print(f"Not enough coins! You have {balance} RPC")
            return False

        tx      = coin.functions.transfer(to_address, amount).transact({"from": sender, "gas": 200000})
        receipt = w3.eth.wait_for_transaction_receipt(tx)
        print(f"Transferred {amount} RPC to {to_address}")
        print(f"TX Hash : {receipt.transactionHash.hex()}")
        return True
    except Exception as e:
        print(f"Transfer failed: {e}")
        return False

# =====================================================
# ========== VIEW FUNCTIONS ==========
# =====================================================

def check_balance(address):
    try:
        coin_bal = coin.functions.balanceOf(address).call()
        eth_bal  = w3.from_wei(w3.eth.get_balance(address), "ether")
        print(f"Balance for: {address}")
        print(f"   RPC Coins : {coin_bal} RPC")
        print(f"   ETH       : {eth_bal:.4f} ETH")
    except Exception as e:
        print(f"Error: {e}")

def view_all_rewards():
    try:
        count = core.functions.rewardCount().call()
        if count == 0:
            print("No rewards available!")
            return
        print("\nAvailable Rewards:")
        print(f"{'ID':<5} {'Name':<20} {'Cost':<10}")
        print("-" * 40)
        for i in range(1, count + 1):
            try:
                reward = core.functions.getReward(i).call()
                print(f"{i:<5} {reward[0]:<20} {reward[1]:<10} coins")
            except:
                continue
    except Exception as e:
        print(f"Error: {e}")

def view_reward(reward_id):
    try:
        reward = core.functions.getReward(reward_id).call()
        if reward[0] == "":
            print("Reward does not exist!")
            return
        print("\n========== REWARD DETAILS ==========")
        print(f"ID   : {reward_id}")
        print(f"Name : {reward[0]}")
        print(f"Cost : {reward[1]} coins")
        print("====================================")
    except Exception as e:
        print(f"Reward not found: {e}")


if __name__ == "__main__":
    print("\n===== TEST FLOW START =====")

    user = w3.eth.accounts[1]

    print("\n1- Register User")
    user_register("Test User", user)

    print("\n2- View Rewards")
    view_all_rewards()

    print("\n3- Check Balance (Before)")
    check_balance(user)

    print("\n4- Mint Coins")
    admin_mint_coins(user, 100)

    print("\n5- Check Balance (After Mint)")
    check_balance(user)

    print("\n6- Buy Reward")
    user_buy_reward(1, user)

    print("\n7- Final Balance")
    check_balance(user)

    print("\n===== TEST FLOW END =====")

  
