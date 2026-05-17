import os
import sys
from web3.logs import DISCARD

# ========== IMPORT TRANSACTION SENDER ==========
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from transaction_sender import (
    w3, core, coin, ADMIN,
    admin_add_reward, admin_update_reward,
    admin_give_coins, admin_mint_coins,
    admin_pause, admin_resume,
    admin_transfer_ownership,
    admin_batch_update,
    user_buy_reward, user_register,
    get_user_name, is_registered,
    check_balance, view_all_rewards, view_reward,
    user_transfer_coins
)

# ========== COLORS ==========
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# ========== CLEAR SCREEN ==========
def clear():
    os.system("cls" if os.name == "nt" else "clear")

# ========== HEADER ==========
def print_header(username="Guest"):
    clear()
    print(f"{CYAN}{BOLD}")
    print("=" * 45)
    print("    STORE REWARDS & POINTS SYSTEM")
    print("    Blockchain-Powered Loyalty App")
    print("=" * 45)
    print(f"    Welcome, {username}")
    print("=" * 45)
    print(f"{RESET}")

# =====================================================
# ========== PERSONAL ACTIVITY HISTORY ==========
# =====================================================
def view_activity_history(address):
    try:
        print(f"\n  Scanning blockchain for: {address}")
        print(f"  Please wait...\n")

        latest = w3.eth.block_number
        history = []

        for block_num in range(0, latest + 1):
            block = w3.eth.get_block(block_num, full_transactions=True)
            for tx in block.transactions:
                if (tx["from"].lower() == address.lower() or
                        (tx["to"] and tx["to"].lower() == address.lower())):

                    # تحديد نوع العملية
                    if tx["to"] and tx["to"].lower() == CORE_ADDRESS.lower():
                        action = "Contract Interaction"
                        # نحاول نحدد اكتر
                        input_data = tx["input"]
                        input_hex = input_data.hex() if hasattr(input_data, "hex") else str(input_data)
                        if not input_hex.startswith("0x"):
                            input_hex = "0x" + input_hex

                        buy_reward_sig = "0x" + w3.keccak(text="buyReward(uint256)")[:4].hex()
                        if input_hex[:10] == buy_reward_sig:
                            action = "Buy Reward"
                        else:
                            action = "Contract Call"
                    elif tx["to"] and tx["to"].lower() == COIN_ADDRESS.lower():
                        action = "Coin Transaction"
                    elif tx["from"].lower() == address.lower():
                        action = "ETH Transfer (Out)"
                    else:
                        action = "ETH Transfer (In)"

                    history.append({
                        "block": block_num,
                        "action": action,
                        "from": tx["from"],
                        "to": tx["to"],
                        "value": w3.from_wei(tx["value"], "ether")
                    })

        if not history:
            print(f"  No transactions found for this address.")
            return

        print(f"  {'Block':<8} {'Action':<25} {'Value (ETH)':<12}")
        print("  " + "-" * 50)
        for h in history:
            print(f"  {h['block']:<8} {h['action']:<25} {h['value']:<12.4f}")

        print(f"\n  Total Transactions: {len(history)}")

    except Exception as e:
        print(f"{RED}  Error scanning blockchain: {e}{RESET}")

# =====================================================
# ========== COIN ADDRESS (needed for history) ==========
# =====================================================
CORE_ADDRESS = core.address
COIN_ADDRESS = coin.address

def view_activity_history(address):
    try:
        address = w3.to_checksum_address(address)
        print(f"\n  Scanning blockchain for: {address}")
        print(f"  Please wait...\n")

        latest = w3.eth.block_number
        history = []
        zero_address = "0x0000000000000000000000000000000000000000"

        for block_num in range(0, latest + 1):
            block = w3.eth.get_block(block_num, full_transactions=True)
            for tx in block.transactions:
                tx_to = tx["to"]
                tx_from = tx["from"]
                eth_value = w3.from_wei(tx["value"], "ether")
                matched_event = False
                purchase_event_for_user = False

                if tx_to and tx_to.lower() in [CORE_ADDRESS.lower(), COIN_ADDRESS.lower()]:
                    receipt = w3.eth.get_transaction_receipt(tx.hash)

                    try:
                        for evt in core.events.UserRegistered().process_receipt(receipt, errors=DISCARD):
                            if evt["args"]["user"].lower() == address.lower():
                                history.append({
                                    "block": block_num,
                                    "action": "Registered User",
                                    "rpc": "-",
                                    "eth": f"{eth_value:.4f} ETH"
                                })
                                matched_event = True
                    except Exception:
                        pass

                    try:
                        for evt in core.events.RewardPurchased().process_receipt(receipt, errors=DISCARD):
                            if evt["args"]["user"].lower() == address.lower():
                                cost = evt["args"]["cost"]
                                history.append({
                                    "block": block_num,
                                    "action": "Buy Reward",
                                    "rpc": f"-{cost} RPC",
                                    "eth": f"{eth_value:.4f} ETH"
                                })
                                matched_event = True
                                purchase_event_for_user = True
                    except Exception:
                        pass

                    if not purchase_event_for_user:
                        try:
                            for evt in coin.events.Transfer().process_receipt(receipt, errors=DISCARD):
                                from_addr = evt["args"]["from"]
                                to_addr = evt["args"]["to"]
                                amount = evt["args"]["amount"]

                                if to_addr.lower() == address.lower():
                                    action = "Received Coins"
                                    if from_addr.lower() == zero_address:
                                        action = "Minted Coins"
                                    history.append({
                                        "block": block_num,
                                        "action": action,
                                        "rpc": f"+{amount} RPC",
                                        "eth": f"{eth_value:.4f} ETH"
                                    })
                                    matched_event = True
                                elif from_addr.lower() == address.lower():
                                    history.append({
                                        "block": block_num,
                                        "action": "Sent Coins",
                                        "rpc": f"-{amount} RPC",
                                        "eth": f"{eth_value:.4f} ETH"
                                    })
                                    matched_event = True
                        except Exception:
                            pass

                    try:
                        for evt in coin.events.Approval().process_receipt(receipt, errors=DISCARD):
                            if evt["args"]["owner"].lower() == address.lower():
                                amount = evt["args"]["amount"]
                                history.append({
                                    "block": block_num,
                                    "action": "Approved Coins",
                                    "rpc": f"{amount} RPC",
                                    "eth": f"{eth_value:.4f} ETH"
                                })
                                matched_event = True
                    except Exception:
                        pass

                if not matched_event and (
                    tx_from.lower() == address.lower()
                    or (tx_to and tx_to.lower() == address.lower())
                ):
                    if eth_value > 0:
                        action = "ETH Transfer Out" if tx_from.lower() == address.lower() else "ETH Transfer In"
                    elif tx_to and tx_to.lower() == CORE_ADDRESS.lower():
                        action = "Contract Call"
                    elif tx_to and tx_to.lower() == COIN_ADDRESS.lower():
                        action = "Coin Contract Call"
                    else:
                        action = "Transaction"

                    history.append({
                        "block": block_num,
                        "action": action,
                        "rpc": "-",
                        "eth": f"{eth_value:.4f} ETH"
                    })

        if not history:
            print(f"  No transactions found for this address.")
            return

        print(f"  {'Block':<8} {'Action':<22} {'RPC Value':<15} {'ETH Value':<12}")
        print("  " + "-" * 65)
        for h in history:
            print(f"  {h['block']:<8} {h['action']:<22} {h['rpc']:<15} {h['eth']:<12}")

        print(f"\n  Total Transactions: {len(history)}")

    except Exception as e:
        print(f"{RED}  Error scanning blockchain: {e}{RESET}")

# =====================================================
# ========== MAIN MENU ==========
# =====================================================
def main_menu(username, user_address):
    while True:
        print_header(username)
        print(f"{YELLOW}  MAIN MENU{RESET}")
        print("  1. View Available Rewards")
        print("  2. Buy a Reward")
        print("  3. Check My Balance")
        print("  4. Transfer Coins")
        print("  5. View Single Reward")
        print("  6. Check Any Address Balance")
        print("  7. View Address Activity History")
        print("  0. Exit")

        print(f"\n{CYAN}  Type 'admin' for Admin Panel{RESET}")
        print("-" * 45)

        choice = input("  Choose: ").strip()

        if choice == "1":
            print_header(username)
            view_all_rewards()
            input("\n  Press Enter to continue...")

        elif choice == "2":
            print_header(username)
            view_all_rewards()
            try:
                reward_id = int(input("\n  Enter Reward ID to buy: "))
                user_buy_reward(reward_id, user_address)
            except ValueError:
                print(f"{RED}  Invalid input!{RESET}")
            input("\n  Press Enter to continue...")

        elif choice == "3":
            print_header(username)
            check_balance(user_address)
            input("\n  Press Enter to continue...")

        elif choice == "4":
            print_header(username)
            try:
                to_addr = input("  Enter recipient address: ").strip()
                amount  = int(input("  Enter amount to transfer: "))
                user_transfer_coins(to_addr, amount, user_address)
            except ValueError:
                print(f"{RED}  Invalid input!{RESET}")
            except Exception as e:
                print(f"{RED}  Error: {e}{RESET}")
            input("\n  Press Enter to continue...")

        elif choice == "5":
            print_header(username)
            try:
                reward_id = int(input("  Enter Reward ID: "))
                view_reward(reward_id)
            except ValueError:
                print(f"{RED}  Invalid input!{RESET}")
            input("\n  Press Enter to continue...")

        elif choice == "6":
            # Coin & ETH Balance Checker — أي address
            print_header(username)
            addr = input("  Enter address to check: ").strip()
            try:
                addr = w3.to_checksum_address(addr)
                check_balance(addr)
            except Exception as e:
                print(f"{RED}  Invalid address: {e}{RESET}")
            input("\n  Press Enter to continue...")

        elif choice == "7":
            # Personal Activity History
            print_header(username)
            addr = input("  Enter address to view history: ").strip()
            try:
                addr = w3.to_checksum_address(addr)
                view_activity_history(addr)
            except Exception as e:
                print(f"{RED}  Invalid address: {e}{RESET}")
            input("\n  Press Enter to continue...")

        elif choice.lower() == "admin":
            admin_login(username, user_address)

        elif choice == "0":
            print(f"\n{GREEN}  Goodbye, {username}! See you soon!{RESET}\n")
            break

        else:
            print(f"{RED}  Invalid choice!{RESET}")
            input("  Press Enter to continue...")

# =====================================================
# ========== ADMIN LOGIN ==========
# =====================================================
def admin_login(username, user_address):
    print_header(username)
    print(f"{RED}{BOLD}  ADMIN PANEL - RESTRICTED ACCESS{RESET}")
    print("-" * 45)

    ADMIN_PASSWORD = "crypto2024"
    password = input("  Enter Admin Password: ").strip()

    if password == ADMIN_PASSWORD:
        actual_admin = core.functions.getAdmin().call().lower()
        if actual_admin != user_address.lower():
            print(f"{RED}  Your address is not the admin!{RESET}")
            input("  Press Enter to continue...")
            return
        print(f"{GREEN}  Access Granted!{RESET}")
        input("  Press Enter to enter Admin Panel...")
        admin_menu(username, user_address)
    else:
        print(f"{RED}  Wrong Password! Access Denied!{RESET}")
        input("  Press Enter to continue...")

# =====================================================
# ========== ADMIN MENU ==========
# =====================================================
def admin_menu(username, admin_address):
    while True:
        print_header(username)
        print(f"{RED}{BOLD}  ADMIN PANEL{RESET}")
        print("  1. Add Reward")
        print("  2. Update Reward")
        print("  3. Batch Add Rewards")
        print("  4. Give Coins to User")
        print("  5. View All Rewards")
        print("  6. Check Any User Balance")
        print("  7. View User Activity History")
        print("  8. Pause Contract")
        print("  9. Resume Contract")
        print("  10. Transfer Ownership")
        print("  11. Batch Update Rewards")
        print("  0. Back to Main Menu")
        print("-" * 45)

        choice = input("  Choose: ").strip()

        if choice == "1":
            print_header(username)
            name = input("  Reward Name: ").strip()
            try:
                cost = int(input("  Reward Cost (coins): "))
                admin_add_reward(name, cost, admin_address)
            except ValueError:
                print(f"{RED}  Invalid cost!{RESET}")
            input("\n  Press Enter to continue...")

        elif choice == "2":
            print_header(username)
            view_all_rewards()
            try:
                rid      = int(input("\n  Reward ID to update: "))
                new_name = input("  New Name: ").strip()
                new_cost = int(input("  New Cost: "))
                admin_update_reward(rid, new_name, new_cost, admin_address)
            except ValueError:
                print(f"{RED}  Invalid input!{RESET}")
            input("\n  Press Enter to continue...")

        elif choice == "3":
            print_header(username)
            print("  Enter rewards (type 'done' when finished)")
            names = []
            costs = []
            while True:
                name = input("  Reward Name (or 'done'): ").strip()
                if name.lower() == "done":
                    break
                try:
                    cost = int(input(f"  Cost for '{name}': "))
                    names.append(name)
                    costs.append(cost)
                except ValueError:
                    print(f"{RED}  Invalid cost, skipping!{RESET}")
            if names:
                from transaction_sender import admin_batch_add
                admin_batch_add(names, costs, admin_address)
            input("\n  Press Enter to continue...")

        elif choice == "4":
            print_header(username)
            user_addr = input("  User Address: ").strip()
            try:
                amount = int(input("  Amount of coins: "))
                admin_give_coins(user_addr, amount, admin_address)
            except ValueError:
                print(f"{RED}  Invalid amount!{RESET}")
            input("\n  Press Enter to continue...")

        elif choice == "5":
            print_header(username)
            view_all_rewards()
            input("\n  Press Enter to continue...")

        elif choice == "6":
            print_header(username)
            user_addr = input("  User Address: ").strip()
            try:
                user_addr = w3.to_checksum_address(user_addr)
                check_balance(user_addr)
            except Exception as e:
                print(f"{RED}  Invalid address: {e}{RESET}")
            input("\n  Press Enter to continue...")

        elif choice == "7":
            print_header(username)
            user_addr = input("  Enter Address to view history: ").strip()
            try:
                user_addr = w3.to_checksum_address(user_addr)
                view_activity_history(user_addr)
            except Exception as e:
                print(f"{RED}  Invalid address: {e}{RESET}")
            input("\n  Press Enter to continue...")

        elif choice == "8":
            print_header(username)
            confirm = input("  Pause contract? (yes/no): ").strip()
            if confirm.lower() == "yes":
                admin_pause(admin_address)
            input("\n  Press Enter to continue...")

        elif choice == "9":
            print_header(username)
            confirm = input("  Resume contract? (yes/no): ").strip()
            if confirm.lower() == "yes":
                admin_resume(admin_address)
            input("\n  Press Enter to continue...")

        elif choice == "10":
            print_header(username)
            new_addr = input("  New Admin Address: ").strip()
            confirm  = input(f"  Transfer to {new_addr}? (yes/no): ").strip()
            if confirm.lower() == "yes":
                admin_transfer_ownership(new_addr, admin_address)
                admin_address = w3.to_checksum_address(new_addr)
            input("\n  Press Enter to continue...")

        elif choice == "11":
            print_header(username)
            view_all_rewards()
            print("\n  Enter reward updates (type 'done' when finished)")
            ids = []
            names = []
            costs = []
            while True:
                raw_id = input("  Reward ID (or 'done'): ").strip()
                if raw_id.lower() == "done":
                    break
                try:
                    rid = int(raw_id)
                    name = input("  New Reward Name: ").strip()
                    cost = int(input("  New Reward Cost: "))
                    ids.append(rid)
                    names.append(name)
                    costs.append(cost)
                except ValueError:
                    print(f"{RED}  Invalid input, skipping!{RESET}")
            if ids:
                admin_batch_update(ids, names, costs, admin_address)
            input("\n  Press Enter to continue...")

        elif choice == "0":
            break

        else:
            print(f"{RED}  Invalid choice!{RESET}")
            input("  Press Enter to continue...")

# =====================================================
# ========== LOGIN + REGISTRATION ==========
# =====================================================
def login():
    clear()
    print(f"{CYAN}{BOLD}")
    print("=" * 45)
    print("    STORE REWARDS & POINTS SYSTEM")
    print("=" * 45)
    print(f"{RESET}")
    print("  Please enter your details to continue")
    print("-" * 45)

    print(f"\n  Available accounts:")
    for i, acc in enumerate(w3.eth.accounts[:5]):
        print(f"  {i+1}. {acc}")

    print("-" * 45)
    try:
        choice = int(input("  Select account number (1-5): ")) - 1
        if 0 <= choice <= 4:
            user_address = w3.eth.accounts[choice]
        else:
            print(f"{RED}  Invalid choice! Using account 1{RESET}")
            user_address = w3.eth.accounts[0]
    except ValueError:
        user_address = w3.eth.accounts[0]

    # ===== CHECK REGISTRATION =====
    if is_registered(user_address):
        # الـ user مسجّل — جيب اسمه من الـ contract
        username = get_user_name(user_address)
        print(f"\n{GREEN}  Welcome back, {username}!{RESET}")
    else:
        # أول مرة — اسأله يسجّل
        print(f"\n{YELLOW}  First time here! Please register.{RESET}")
        username = input("  Enter your name: ").strip()
        if not username:
            username = "Guest"
        reg_ok = user_register(username, user_address)
        if not reg_ok:
            # لو فشل التسجيل على الـ contract استخدم الاسم بس
            print(f"{YELLOW}  Continuing without on-chain registration.{RESET}")

    print(f"  Address: {user_address}")
    input("  Press Enter to continue...")
    return username, user_address

# =====================================================
# ========== MAIN ==========
# =====================================================
if __name__ == "__main__":
    try:
        username, user_address = login()
        main_menu(username, user_address)
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}  App closed.{RESET}\n")
