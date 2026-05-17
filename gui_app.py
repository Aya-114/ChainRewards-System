import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
from collections import Counter
import csv

from solcx import compile_source, install_solc
from web3 import Web3
from web3.logs import DISCARD

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = SCRIPT_DIR
if not os.path.isdir(os.path.join(PROJECT_DIR, "contracts")):
    PROJECT_DIR = os.path.join(SCRIPT_DIR, "project Crypto")
os.chdir(PROJECT_DIR)

RPC_URL = "HTTP://127.0.0.1:7545"
ADMIN_PASSWORD = "crypto2024"

# ─── Color Palette ────────────────────────────────────────────────────────────
BG_DEEP    = "#0a0e14"
BG_PANEL   = "#0f1520"
BG_CARD    = "#141c28"
BG_HOVER   = "#1a2535"
BG_INPUT   = "#0d1219"

FG_PRIMARY = "#e8f4e8"
FG_DIM     = "#7a9070"
FG_MUTED   = "#3d5038"

ACCENT_G   = "#39d353"   # neon green
ACCENT_A   = "#f0a500"   # amber
ACCENT_R   = "#e05252"   # red/danger
ACCENT_B   = "#4ca0d0"   # blue/info

BORDER     = "#1e2d1e"
BORDER_HI  = "#2a4a2a"


class BlockchainClient:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not self.w3.is_connected():
            raise RuntimeError("Ganache is not connected on HTTP://127.0.0.1:7545")
        self.addresses = self._load_addresses()
        install_solc("0.8.0")
        self.core = self._load_core_contract()
        self.coin = self._load_coin_contract()

    def _load_addresses(self):
        addresses = {}
        with open("contract_addresses.txt", "r") as f:
            for line in f:
                key, value = line.strip().split("=")
                addresses[key] = value
        return addresses

    def _load_core_contract(self):
        with open("contracts/StoreRewards.sol", "r", encoding="utf-8") as f:
            source = f.read()
        abi = compile_source(source, output_values=["abi"], solc_version="0.8.0")["<stdin>:StoreRewards"]["abi"]
        return self.w3.eth.contract(address=self.addresses["CORE_ADDRESS"], abi=abi)

    def _load_coin_contract(self):
        with open("contracts/RewardPointCoin.sol", "r", encoding="utf-8") as f:
            source = f.read()
        abi = compile_source(source, output_values=["abi"], solc_version="0.8.0")["<stdin>:RewardPointCoin"]["abi"]
        return self.w3.eth.contract(address=self.addresses["COIN_ADDRESS"], abi=abi)

    def wait(self, tx_hash):
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise RuntimeError("Transaction failed on-chain")
        return receipt


class StoreRewardsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Store Rewards & Points — Blockchain Console")
        self.root.geometry("1280x820")
        self.root.minsize(1100, 700)
        self.root.configure(bg=BG_DEEP)

        try:
            self.client = BlockchainClient()
        except Exception as exc:
            messagebox.showerror("Connection Failed", str(exc))
            raise

        self.w3 = self.client.w3
        self.core = self.client.core
        self.coin = self.client.coin
        self.admin_unlocked = False
        self._pulse_state = False
        self.popular_report_rows = []

        self._apply_theme()
        self._build_layout()
        self.refresh_all()
        self._start_clock()

    # ─── Theme ────────────────────────────────────────────────────────────────
    def _apply_theme(self):
        s = ttk.Style()
        s.theme_use("clam")

        # Notebook
        s.configure("TNotebook", background=BG_DEEP, borderwidth=0, tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab",
                    background=BG_PANEL, foreground=FG_DIM,
                    font=("Courier New", 10, "bold"),
                    padding=[18, 8], borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", BG_CARD)],
              foreground=[("selected", ACCENT_G)])

        # Frames / LabelFrames
        s.configure("TFrame", background=BG_DEEP)
        s.configure("Card.TFrame", background=BG_CARD, relief="flat")
        s.configure("TLabelframe", background=BG_CARD,
                    bordercolor=BORDER_HI, relief="flat",
                    labelmargins=[10, 0, 0, 0])
        s.configure("TLabelframe.Label",
                    background=BG_CARD, foreground=ACCENT_G,
                    font=("Courier New", 9, "bold"))

        # Labels
        s.configure("TLabel", background=BG_CARD, foreground=FG_PRIMARY,
                    font=("Courier New", 10))
        s.configure("Title.TLabel", background=BG_DEEP, foreground=ACCENT_G,
                    font=("Courier New", 18, "bold"))
        s.configure("Sub.TLabel", background=BG_DEEP, foreground=FG_DIM,
                    font=("Courier New", 9))
        s.configure("Stat.TLabel", background=BG_CARD, foreground=ACCENT_A,
                    font=("Courier New", 11, "bold"))
        s.configure("StatLabel.TLabel", background=BG_CARD, foreground=FG_DIM,
                    font=("Courier New", 8))
        s.configure("Profile.TLabel", background=BG_CARD, foreground=FG_PRIMARY,
                    font=("Courier New", 10, "bold"))
        s.configure("Dim.TLabel", background=BG_CARD, foreground=FG_DIM,
                    font=("Courier New", 9))
        s.configure("Balance.TLabel", background=BG_CARD, foreground=ACCENT_G,
                    font=("Courier New", 13, "bold"))
        s.configure("BalanceSub.TLabel", background=BG_CARD, foreground=FG_DIM,
                    font=("Courier New", 8))
        s.configure("AdminStatus.TLabel", background=BG_CARD,
                    font=("Courier New", 9, "bold"))

        # Buttons
        for name, fg, bg, abg in [
            ("TButton",        FG_PRIMARY, BG_PANEL, BG_HOVER),
            ("Green.TButton",  BG_DEEP,    ACCENT_G, "#2ab83f"),
            ("Amber.TButton",  BG_DEEP,    ACCENT_A, "#c88800"),
            ("Red.TButton",    FG_PRIMARY, ACCENT_R, "#bb3333"),
            ("Ghost.TButton",  FG_DIM,     BG_CARD,  BG_HOVER),
        ]:
            s.configure(name, background=bg, foreground=fg,
                        font=("Courier New", 9, "bold"),
                        padding=[10, 6], relief="flat", borderwidth=0)
            s.map(name, background=[("active", abg), ("pressed", abg)])

        # Treeview
        s.configure("Treeview",
                    background=BG_INPUT, foreground=FG_PRIMARY,
                    fieldbackground=BG_INPUT,
                    font=("Courier New", 9),
                    rowheight=26, borderwidth=0)
        s.configure("Treeview.Heading",
                    background=BG_PANEL, foreground=ACCENT_G,
                    font=("Courier New", 9, "bold"),
                    relief="flat", borderwidth=0)
        s.map("Treeview",
              background=[("selected", BORDER_HI)],
              foreground=[("selected", ACCENT_G)])

        # Entry / Combobox
        s.configure("TEntry",
                    fieldbackground=BG_INPUT, foreground=FG_PRIMARY,
                    insertcolor=ACCENT_G,
                    font=("Courier New", 9),
                    padding=[6, 5], relief="flat", borderwidth=1)
        s.configure("TCombobox",
                    fieldbackground=BG_INPUT, foreground=FG_PRIMARY,
                    background=BG_PANEL, selectbackground=BG_HOVER,
                    font=("Courier New", 9))
        s.map("TCombobox", fieldbackground=[("readonly", BG_INPUT)])

        # Scrollbar
        s.configure("Vertical.TScrollbar",
                    background=BG_PANEL, troughcolor=BG_INPUT,
                    arrowcolor=FG_DIM, relief="flat", borderwidth=0)

        # Separator
        s.configure("TSeparator", background=BORDER)

    # ─── Layout ───────────────────────────────────────────────────────────────
    def _build_layout(self):
        # ── Top bar ──────────────────────────────────────────
        topbar = tk.Frame(self.root, bg=BG_DEEP, pady=14)
        topbar.pack(fill="x", padx=16)

        left_head = tk.Frame(topbar, bg=BG_DEEP)
        left_head.pack(side="left")

        self._dot = tk.Label(left_head, text="●", fg=ACCENT_G, bg=BG_DEEP,
                             font=("Courier New", 14))
        self._dot.pack(side="left", padx=(0, 8))

        ttk.Label(left_head, text="STORE REWARDS & POINTS",
                  style="Title.TLabel").pack(side="left")

        self._clock_var = tk.StringVar()
        tk.Label(topbar, textvariable=self._clock_var, bg=BG_DEEP,
                 fg=FG_DIM, font=("Courier New", 9)).pack(side="right", padx=(0, 4))

        # ── Status / account bar ─────────────────────────────
        acctbar = tk.Frame(self.root, bg=BG_PANEL, pady=8)
        acctbar.pack(fill="x", padx=0)

        inner = tk.Frame(acctbar, bg=BG_PANEL)
        inner.pack(fill="x", padx=16)

        tk.Label(inner, text="ACCOUNT", bg=BG_PANEL, fg=FG_DIM,
                 font=("Courier New", 8, "bold")).pack(side="left", padx=(0, 8))

        self.account_var = tk.StringVar()
        self.account_combo = ttk.Combobox(
            inner, textvariable=self.account_var,
            values=self._account_options(), width=60, state="readonly"
        )
        self.account_combo.pack(side="left")
        self.account_combo.current(0)
        self.account_combo.bind("<<ComboboxSelected>>", lambda _: self._on_account_changed())

        ttk.Button(inner, text="⟳ REFRESH", style="Ghost.TButton",
                   command=self.refresh_all).pack(side="left", padx=(10, 0))

        # Live balance pills
        self._rpc_pill_var = tk.StringVar(value="— RPC")
        self._eth_pill_var = tk.StringVar(value="— ETH")

        for icon, var, color in [("◈", self._rpc_pill_var, ACCENT_G),
                                  ("◆", self._eth_pill_var, ACCENT_B)]:
            f = tk.Frame(inner, bg=BG_PANEL)
            f.pack(side="right", padx=(8, 0))
            tk.Label(f, text=icon, bg=BG_PANEL, fg=color,
                     font=("Courier New", 10)).pack(side="left", padx=(0, 4))
            v_lbl = tk.Label(f, textvariable=var, bg=BG_PANEL, fg=color,
                             font=("Courier New", 10, "bold"))
            v_lbl.pack(side="left")

        # Status message
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Frame(self.root, bg=BG_DEEP)
        status_bar.pack(fill="x", padx=16, pady=(4, 0))
        tk.Label(status_bar, text="›", bg=BG_DEEP, fg=ACCENT_G,
                 font=("Courier New", 10, "bold")).pack(side="left")
        tk.Label(status_bar, textvariable=self.status_var, bg=BG_DEEP,
                 fg=FG_DIM, font=("Courier New", 9)).pack(side="left", padx=(4, 0))

        # ── Notebook ──────────────────────────────────────────
        sep = ttk.Separator(self.root, orient="horizontal")
        sep.pack(fill="x", padx=0, pady=(6, 0))

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=0, pady=0)

        def _make_tab(text):
            f = ttk.Frame(self.notebook)
            self.notebook.add(f, text=f"  {text}  ")
            f.configure(style="TFrame")
            # Give inner padding via a wrapper
            inner_f = tk.Frame(f, bg=BG_DEEP)
            inner_f.pack(fill="both", expand=True, padx=14, pady=14)
            return inner_f

        self.user_tab   = _make_tab("USER")
        self.admin_tab  = _make_tab("ADMIN")
        self.system_tab = _make_tab("SYSTEM")
        self.log_tab    = _make_tab("LOG")

        self._build_user_tab()
        self._build_admin_tab()
        self._build_system_tab()
        self._build_log_tab()

    # ─── User Tab ─────────────────────────────────────────────────────────────
    def _build_user_tab(self):
        p = self.user_tab
        p.columnconfigure(0, weight=5)
        p.columnconfigure(1, weight=3)
        p.rowconfigure(1, weight=1)

        # ── Profile card ──────────────────────────────────────
        prof = tk.Frame(p, bg=BG_CARD, bd=0, highlightthickness=1,
                        highlightbackground=BORDER_HI)
        prof.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        prof_inner = tk.Frame(prof, bg=BG_CARD)
        prof_inner.pack(fill="x", padx=14, pady=10)

        self.profile_var = tk.StringVar(value="— Not registered")
        tk.Label(prof_inner, textvariable=self.profile_var, bg=BG_CARD,
                 fg=FG_PRIMARY, font=("Courier New", 11, "bold")).pack(side="left")

        reg_f = tk.Frame(prof_inner, bg=BG_CARD)
        reg_f.pack(side="right")
        self.register_name_var = tk.StringVar()
        ttk.Entry(reg_f, textvariable=self.register_name_var, width=22).pack(side="left", padx=(0, 6))
        ttk.Button(reg_f, text="REGISTER", style="Green.TButton",
                   command=self._register_current_user).pack(side="left", padx=(0, 6))
        ttk.Button(reg_f, text="MY BALANCE", style="Ghost.TButton",
                   command=self._show_my_balance).pack(side="left")

        # ── Rewards list ──────────────────────────────────────
        rew_frame = tk.Frame(p, bg=BG_CARD, highlightthickness=1,
                             highlightbackground=BORDER_HI)
        rew_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        rew_frame.rowconfigure(1, weight=1)
        rew_frame.columnconfigure(0, weight=1)

        rew_head = tk.Frame(rew_frame, bg=BG_PANEL, padx=12, pady=8)
        rew_head.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(rew_head, text="AVAILABLE REWARDS", bg=BG_PANEL,
                 fg=ACCENT_G, font=("Courier New", 10, "bold")).pack(side="left")
        ttk.Button(rew_head, text="⟳", style="Ghost.TButton",
                   command=self._refresh_rewards).pack(side="right")
        ttk.Button(rew_head, text="BUY SELECTED ▶",
                   style="Green.TButton",
                   command=self._buy_selected_reward).pack(side="right", padx=(0, 6))

        self.rewards_tree = ttk.Treeview(
            rew_frame, columns=("id", "name", "cost"),
            show="headings", selectmode="browse"
        )
        self.rewards_tree.heading("id",   text="ID")
        self.rewards_tree.heading("name", text="REWARD NAME")
        self.rewards_tree.heading("cost", text="COST (RPC)")
        self.rewards_tree.column("id",   width=50,  anchor="center")
        self.rewards_tree.column("name", width=300)
        self.rewards_tree.column("cost", width=100, anchor="center")
        self.rewards_tree.grid(row=1, column=0, sticky="nsew")

        rew_scroll = ttk.Scrollbar(rew_frame, orient="vertical",
                                   command=self.rewards_tree.yview)
        rew_scroll.grid(row=1, column=1, sticky="ns")
        self.rewards_tree.configure(yscrollcommand=rew_scroll.set)

        # ── Right column ──────────────────────────────────────
        right = tk.Frame(p, bg=BG_DEEP)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        # Balance checker card
        bal_card = self._card(right, "BALANCE CHECKER")
        bal_card.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        bal_card.columnconfigure(0, weight=1)

        self.balance_address_var = tk.StringVar()
        addr_row = tk.Frame(bal_card, bg=BG_CARD)
        addr_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        addr_row.columnconfigure(0, weight=1)
        ttk.Entry(addr_row, textvariable=self.balance_address_var).grid(
            row=0, column=0, sticky="ew")
        ttk.Button(addr_row, text="CHECK", style="Ghost.TButton",
                   command=self._check_address_balance).grid(row=0, column=1, padx=(6, 0))

        self.balance_result_var = tk.StringVar(value="—")
        tk.Label(bal_card, textvariable=self.balance_result_var,
                 bg=BG_CARD, fg=ACCENT_G,
                 font=("Courier New", 11, "bold")).grid(row=1, column=0, sticky="w")

        # Transfer card
        xfer_card = self._card(right, "TRANSFER COINS")
        xfer_card.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        xfer_card.columnconfigure(1, weight=1)

        for i, (lbl, var_attr, w) in enumerate([
            ("TO",     "transfer_to_var",     None),
            ("AMOUNT", "transfer_amount_var", 14),
        ]):
            tk.Label(xfer_card, text=lbl, bg=BG_CARD, fg=FG_DIM,
                     font=("Courier New", 8, "bold")).grid(
                row=i, column=0, sticky="w", pady=(4, 0))
            setattr(self, var_attr, tk.StringVar())
            kw = {"width": w} if w else {}
            ttk.Entry(xfer_card, textvariable=getattr(self, var_attr),
                      **kw).grid(row=i, column=1, sticky="ew", padx=(8, 0), pady=(4, 0))

        ttk.Button(xfer_card, text="SEND ▶", style="Amber.TButton",
                   command=self._transfer_coins).grid(
            row=2, column=1, sticky="w", padx=(8, 0), pady=(10, 4))

        # History card
        hist_card = self._card(right, "ACTIVITY HISTORY")
        hist_card.grid(row=2, column=0, sticky="nsew")
        hist_card.rowconfigure(1, weight=1)
        hist_card.columnconfigure(0, weight=1)

        hist_ctrl = tk.Frame(hist_card, bg=BG_CARD)
        hist_ctrl.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        hist_ctrl.columnconfigure(0, weight=1)
        self.history_address_var = tk.StringVar()
        ttk.Entry(hist_ctrl, textvariable=self.history_address_var).grid(
            row=0, column=0, sticky="ew")
        ttk.Button(hist_ctrl, text="LOAD", style="Ghost.TButton",
                   command=self._load_history).grid(row=0, column=1, padx=(6, 0))

        self.history_tree = ttk.Treeview(
            hist_card, columns=("block", "action", "rpc", "eth"),
            show="headings"
        )
        for col, txt, w in [("block","BLK",60),("action","ACTION",150),
                             ("rpc","RPC",90),("eth","ETH",80)]:
            self.history_tree.heading(col, text=txt)
            self.history_tree.column(col, width=w)
        self.history_tree.grid(row=1, column=0, sticky="nsew")

    # ─── Admin Tab ────────────────────────────────────────────────────────────
    def _build_admin_tab(self):
        p = self.admin_tab
        p.columnconfigure(0, weight=1)
        p.columnconfigure(1, weight=1)
        p.rowconfigure(2, weight=1)

        # ── Auth row ──────────────────────────────────────────
        auth = tk.Frame(p, bg=BG_CARD, highlightthickness=1,
                        highlightbackground=BORDER_HI)
        auth.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        auth_inner = tk.Frame(auth, bg=BG_CARD)
        auth_inner.pack(fill="x", padx=14, pady=10)

        tk.Label(auth_inner, text="🔐  ADMIN AUTH", bg=BG_CARD, fg=ACCENT_A,
                 font=("Courier New", 10, "bold")).pack(side="left")

        self.admin_password_var = tk.StringVar()
        ttk.Entry(auth_inner, textvariable=self.admin_password_var,
                  show="●", width=24).pack(side="left", padx=(16, 6))
        ttk.Button(auth_inner, text="UNLOCK", style="Amber.TButton",
                   command=self._unlock_admin).pack(side="left")

        self._admin_led = tk.Label(auth_inner, text="  ●  LOCKED",
                                   bg=BG_CARD, fg=ACCENT_R,
                                   font=("Courier New", 9, "bold"))
        self._admin_led.pack(side="right")

        self.admin_status_var = tk.StringVar(value="Locked")

        # ── Single Reward ──────────────────────────────────────
        rew_card = self._card(p, "SINGLE REWARD")
        rew_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        rew_card.columnconfigure(1, weight=1)

        self.admin_reward_name_var = tk.StringVar()
        self.admin_reward_cost_var = tk.StringVar()

        for i, (lbl, var) in enumerate([("NAME", self.admin_reward_name_var),
                                         ("COST", self.admin_reward_cost_var)]):
            tk.Label(rew_card, text=lbl, bg=BG_CARD, fg=FG_DIM,
                     font=("Courier New", 8, "bold")).grid(
                row=i, column=0, sticky="w", pady=(4, 0))
            ttk.Entry(rew_card, textvariable=var).grid(
                row=i, column=1, sticky="ew", padx=(8, 0), pady=(4, 0))

        btn_row = tk.Frame(rew_card, bg=BG_CARD)
        btn_row.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 4))
        ttk.Button(btn_row, text="ADD REWARD", style="Green.TButton",
                   command=self._admin_add_reward).pack(side="left")
        ttk.Button(btn_row, text="UPDATE SELECTED", style="Ghost.TButton",
                   command=self._admin_update_selected_reward).pack(side="left", padx=(8, 0))

        # ── Coins & Control ──────────────────────────────────
        ctrl_card = self._card(p, "COINS & CONTROL")
        ctrl_card.grid(row=1, column=1, sticky="nsew", pady=(0, 8))
        ctrl_card.columnconfigure(1, weight=1)

        self.mint_to_var     = tk.StringVar()
        self.mint_amount_var = tk.StringVar()

        for i, (lbl, var) in enumerate([("USER ADDR", self.mint_to_var),
                                         ("AMOUNT",    self.mint_amount_var)]):
            tk.Label(ctrl_card, text=lbl, bg=BG_CARD, fg=FG_DIM,
                     font=("Courier New", 8, "bold")).grid(
                row=i, column=0, sticky="w", pady=(4, 0))
            ttk.Entry(ctrl_card, textvariable=var).grid(
                row=i, column=1, sticky="ew", padx=(8, 0), pady=(4, 0))

        ttk.Button(ctrl_card, text="GIVE COINS", style="Amber.TButton",
                   command=self._admin_give_coins).grid(
            row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 4))

        sep = tk.Frame(ctrl_card, bg=BORDER, height=1)
        sep.grid(row=3, column=0, columnspan=2, sticky="ew", pady=8)

        pause_row = tk.Frame(ctrl_card, bg=BG_CARD)
        pause_row.grid(row=4, column=0, columnspan=2, sticky="w")
        ttk.Button(pause_row, text="⏸ PAUSE", style="Red.TButton",
                   command=self._admin_pause).pack(side="left")
        ttk.Button(pause_row, text="▶ RESUME", style="Green.TButton",
                   command=self._admin_resume).pack(side="left", padx=(8, 0))

        sep2 = tk.Frame(ctrl_card, bg=BORDER, height=1)
        sep2.grid(row=5, column=0, columnspan=2, sticky="ew", pady=8)

        tk.Label(ctrl_card, text="NEW ADMIN", bg=BG_CARD, fg=FG_DIM,
                 font=("Courier New", 8, "bold")).grid(row=6, column=0, sticky="w")
        self.new_admin_var = tk.StringVar()
        ttk.Entry(ctrl_card, textvariable=self.new_admin_var).grid(
            row=6, column=1, sticky="ew", padx=(8, 0))
        ttk.Button(ctrl_card, text="TRANSFER OWNERSHIP", style="Red.TButton",
                   command=self._admin_transfer_ownership).grid(
            row=7, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        # ── Batch ops ─────────────────────────────────────────
        batch_add = self._card(p, "BATCH ADD  (name, cost — one per line)")
        batch_add.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        batch_add.rowconfigure(0, weight=1)
        batch_add.columnconfigure(0, weight=1)

        self.batch_add_text = tk.Text(
            batch_add, height=7, bg=BG_INPUT, fg=FG_PRIMARY,
            insertbackground=ACCENT_G, font=("Courier New", 9),
            relief="flat", bd=0, wrap="none"
        )
        self.batch_add_text.grid(row=0, column=0, sticky="nsew")
        ttk.Button(batch_add, text="BATCH ADD REWARDS", style="Green.TButton",
                   command=self._admin_batch_add).grid(
            row=1, column=0, sticky="w", pady=(8, 0))

        batch_upd = self._card(p, "BATCH UPDATE  (id, name, cost — one per line)")
        batch_upd.grid(row=2, column=1, sticky="nsew")
        batch_upd.rowconfigure(0, weight=1)
        batch_upd.columnconfigure(0, weight=1)

        self.batch_update_text = tk.Text(
            batch_upd, height=7, bg=BG_INPUT, fg=FG_PRIMARY,
            insertbackground=ACCENT_G, font=("Courier New", 9),
            relief="flat", bd=0, wrap="none"
        )
        self.batch_update_text.grid(row=0, column=0, sticky="nsew")
        ttk.Button(batch_upd, text="BATCH UPDATE REWARDS", style="Amber.TButton",
                   command=self._admin_batch_update).grid(
            row=1, column=0, sticky="w", pady=(8, 0))

    # ─── System Tab ───────────────────────────────────────────────────────────
    def _build_system_tab(self):
        p = self.system_tab
        p.columnconfigure(0, weight=1)
        p.columnconfigure(1, weight=1)
        p.rowconfigure(1, weight=1)
        p.rowconfigure(2, weight=1)

        # Stat pills row
        stats_row = tk.Frame(p, bg=BG_DEEP)
        stats_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        for i in range(4):
            stats_row.columnconfigure(i, weight=1)

        stat_defs = [
            ("TOTAL REWARDS",  "stat_rewards_var",  ACCENT_G),
            ("TOTAL SUPPLY",   "stat_supply_var",   ACCENT_A),
            ("LATEST BLOCK",   "stat_block_var",    ACCENT_B),
            ("CONTRACT STATE", "stat_state_var",    ACCENT_R),
        ]
        for i, (lbl, attr, color) in enumerate(stat_defs):
            cell = tk.Frame(stats_row, bg=BG_CARD, highlightthickness=1,
                            highlightbackground=BORDER_HI)
            cell.grid(row=0, column=i, sticky="ew", padx=(0 if i==0 else 6, 0))
            tk.Label(cell, text=lbl, bg=BG_CARD, fg=FG_DIM,
                     font=("Courier New", 8, "bold")).pack(pady=(8, 0))
            var = tk.StringVar(value="—")
            setattr(self, attr, var)
            tk.Label(cell, textvariable=var, bg=BG_CARD, fg=color,
                     font=("Courier New", 16, "bold")).pack(pady=(0, 8))

        # Accounts table
        accts_card = self._card(p, "ACCOUNT BALANCES")
        accts_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        accts_card.rowconfigure(0, weight=1)
        accts_card.columnconfigure(0, weight=1)

        self.accts_tree = ttk.Treeview(
            accts_card,
            columns=("num", "address", "rpc", "eth"),
            show="headings"
        )
        for col, txt, w, anc in [
            ("num",     "#",       40,  "center"),
            ("address", "ADDRESS", 300, "w"),
            ("rpc",     "RPC",     90,  "center"),
            ("eth",     "ETH",     90,  "center"),
        ]:
            self.accts_tree.heading(col, text=txt)
            self.accts_tree.column(col, width=w, anchor=anc)
        self.accts_tree.grid(row=0, column=0, sticky="nsew")

        ttk.Button(accts_card, text="EXPORT BALANCE SNAPSHOT", style="Green.TButton",
                   command=self._export_balance_snapshot).grid(
            row=1, column=0, sticky="w", pady=(8, 0))

        # Contract info pane
        info_card = self._card(p, "CONTRACT INFO")
        info_card.grid(row=1, column=1, sticky="nsew")
        info_card.columnconfigure(0, weight=1)
        info_card.rowconfigure(0, weight=1)

        self.system_text = tk.Text(
            info_card, bg=BG_INPUT, fg=FG_PRIMARY,
            insertbackground=ACCENT_G,
            font=("Courier New", 9), relief="flat", bd=0,
            wrap="word", state="disabled"
        )
        self.system_text.grid(row=0, column=0, sticky="nsew")

        sys_scroll = ttk.Scrollbar(info_card, orient="vertical",
                                   command=self.system_text.yview)
        sys_scroll.grid(row=0, column=1, sticky="ns")
        self.system_text.configure(yscrollcommand=sys_scroll.set)

        btn_row = tk.Frame(info_card, bg=BG_CARD)
        btn_row.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Button(btn_row, text="⟳ REFRESH SYSTEM", style="Ghost.TButton",
                   command=self._refresh_system_summary).pack(side="left")

        # Popular reward items from blockchain history
        popular_card = self._card(p, "DATA HISTORY REPORT - MOST POPULAR REWARDS")
        popular_card.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
        popular_card.rowconfigure(0, weight=1)
        popular_card.columnconfigure(0, weight=1)

        self.popular_tree = ttk.Treeview(
            popular_card,
            columns=("rank", "reward", "cost", "purchases"),
            show="headings"
        )
        for col, txt, w, anc in [
            ("rank",      "#",          50,  "center"),
            ("reward",    "REWARD",     360, "w"),
            ("cost",      "COST",       100, "center"),
            ("purchases", "PURCHASES",  120, "center"),
        ]:
            self.popular_tree.heading(col, text=txt)
            self.popular_tree.column(col, width=w, anchor=anc)
        self.popular_tree.grid(row=0, column=0, sticky="nsew")

        popular_scroll = ttk.Scrollbar(popular_card, orient="vertical",
                                       command=self.popular_tree.yview)
        popular_scroll.grid(row=0, column=1, sticky="ns")
        self.popular_tree.configure(yscrollcommand=popular_scroll.set)

        ttk.Button(popular_card, text="SCAN CHAIN HISTORY", style="Ghost.TButton",
                   command=self._refresh_popular_rewards).grid(
            row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Button(popular_card, text="PRINT TABLE", style="Amber.TButton",
                   command=self._print_popular_rewards).grid(
            row=1, column=0, sticky="w", padx=(160, 0), pady=(8, 0))
        ttk.Button(popular_card, text="EXPORT CSV", style="Green.TButton",
                   command=self._export_popular_rewards).grid(
            row=1, column=0, sticky="w", padx=(280, 0), pady=(8, 0))

    # ─── Log Tab ──────────────────────────────────────────────────────────────
    def _build_log_tab(self):
        p = self.log_tab
        p.rowconfigure(0, weight=1)
        p.columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            p, bg=BG_INPUT, fg=ACCENT_G,
            insertbackground=ACCENT_G,
            font=("Courier New", 9), relief="flat", bd=0,
            wrap="word", state="disabled"
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        log_scroll = ttk.Scrollbar(p, orient="vertical",
                                   command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scroll.set)

        btn_row = tk.Frame(p, bg=BG_DEEP)
        btn_row.grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Button(btn_row, text="CLEAR LOG", style="Ghost.TButton",
                   command=self._clear_log).pack(side="left")

    # ─── Helper: card factory ─────────────────────────────────────────────────
    def _card(self, parent, title):
        """Creates a titled card frame with consistent styling."""
        outer = tk.Frame(parent, bg=BG_CARD, highlightthickness=1,
                         highlightbackground=BORDER_HI)
        tk.Label(outer, text=f"  {title}  ", bg=BG_PANEL, fg=ACCENT_G,
                 font=("Courier New", 8, "bold")).grid(row=0, column=0, sticky="ew")
        inner = tk.Frame(outer, bg=BG_CARD)
        inner.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        outer.rowconfigure(1, weight=1)
        outer.columnconfigure(0, weight=1)
        # Place the visible outer card, while callers keep adding widgets to inner.
        inner._outer = outer
        inner.grid = outer.grid
        inner.pack = outer.pack
        inner.place = outer.place
        return inner

    # ─── Clock ────────────────────────────────────────────────────────────────
    def _start_clock(self):
        def tick():
            while True:
                ts = time.strftime("%Y-%m-%d  %H:%M:%S")
                self._clock_var.set(ts)
                time.sleep(1)
        t = threading.Thread(target=tick, daemon=True)
        t.start()

    # ─── Refresh helpers ──────────────────────────────────────────────────────
    def _account_options(self):
        result = []
        for i, acc in enumerate(self.w3.eth.accounts[:5], start=1):
            result.append(f"{i}.  {acc}")
        return result

    def _selected_account(self):
        return self.account_var.get().split("  ", 1)[1]

    def _on_account_changed(self):
        self.admin_unlocked = False
        self._admin_led.config(text="  ●  LOCKED", fg=ACCENT_R)
        self.admin_status_var.set("Locked")
        self.refresh_profile()
        self._update_balance_pills()

    def _update_balance_pills(self):
        try:
            acc = self._selected_account()
            rpc = self.coin.functions.balanceOf(acc).call()
            eth = float(self.w3.from_wei(self.w3.eth.get_balance(acc), "ether"))
            self._rpc_pill_var.set(f"{rpc} RPC")
            self._eth_pill_var.set(f"{eth:.4f} ETH")
        except Exception:
            pass

    def refresh_all(self):
        self.refresh_profile()
        self._refresh_rewards()
        self._refresh_system_summary()
        self._refresh_popular_rewards()
        self._update_balance_pills()
        self.status_var.set("Refreshed at " + time.strftime("%H:%M:%S"))

    def refresh_profile(self):
        try:
            acc = self._selected_account()
            if self.core.functions.isRegistered(acc).call():
                name = self.core.functions.getUserName(acc).call()
                rpc  = self.coin.functions.balanceOf(acc).call()
                eth  = float(self.w3.from_wei(self.w3.eth.get_balance(acc), "ether"))
                self.profile_var.set(
                    f"◈  {name}   |   {rpc} RPC   |   {eth:.4f} ETH   |   {acc[:16]}…"
                )
            else:
                self.profile_var.set(f"⚬  Not registered  —  {acc[:20]}…")
        except Exception:
            pass

    def _refresh_rewards(self):
        try:
            for row in self.rewards_tree.get_children():
                self.rewards_tree.delete(row)
            count = self.core.functions.rewardCount().call()
            for i in range(1, count + 1):
                try:
                    r = self.core.functions.getReward(i).call()
                    self.rewards_tree.insert("", "end", values=(i, r[0], r[1]))
                except Exception:
                    continue
        except Exception as exc:
            messagebox.showerror("Rewards Error", str(exc))

    def _refresh_system_summary(self):
        try:
            rewards = self.core.functions.rewardCount().call()
            supply  = self.coin.functions.totalSupply().call()
            block   = self.w3.eth.block_number
            paused  = self.core.functions.paused().call()

            self.stat_rewards_var.set(str(rewards))
            self.stat_supply_var.set(str(supply))
            self.stat_block_var.set(str(block))
            self.stat_state_var.set("PAUSED" if paused else "LIVE")
            if hasattr(self, "stat_state_var"):
                # recolor state pill
                pass

            # Update accounts table
            for row in self.accts_tree.get_children():
                self.accts_tree.delete(row)
            for i, acc in enumerate(self.w3.eth.accounts[:5], start=1):
                rpc = self.coin.functions.balanceOf(acc).call()
                eth = float(self.w3.from_wei(self.w3.eth.get_balance(acc), "ether"))
                self.accts_tree.insert("", "end", values=(i, acc, rpc, f"{eth:.4f}"))

            # Update text pane
            lines = [
                f"RPC URL   : {RPC_URL}",
                f"Core Addr : {self.core.address}",
                f"Coin Addr : {self.coin.address}",
                f"Core Admin: {self.core.functions.getAdmin().call()}",
                f"Coin Admin: {self.coin.functions.admin().call()}",
                f"Rewards   : {rewards}",
                f"Supply    : {supply} RPC",
                f"Block     : {block}",
                f"Paused    : {paused}",
            ]
            self.system_text.configure(state="normal")
            self.system_text.delete("1.0", "end")
            self.system_text.insert("1.0", "\n".join(lines))
            self.system_text.configure(state="disabled")
        except Exception as exc:
            messagebox.showerror("System Error", str(exc))

    def _refresh_popular_rewards(self):
        try:
            for row in self.popular_tree.get_children():
                self.popular_tree.delete(row)

            latest = self.w3.eth.block_number
            purchase_count = Counter()
            purchase_costs = {}

            for block_num in range(0, latest + 1):
                block = self.w3.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions:
                    if not tx["to"] or tx["to"].lower() != self.core.address.lower():
                        continue

                    receipt = self.w3.eth.get_transaction_receipt(tx.hash)
                    for evt in self.core.events.RewardPurchased().process_receipt(
                            receipt, errors=DISCARD):
                        reward_id = evt["args"]["id"]
                        cost = evt["args"]["cost"]
                        purchase_count[reward_id] += 1
                        purchase_costs[reward_id] = cost

            reward_count = self.core.functions.rewardCount().call()
            rows = []
            for reward_id in range(1, reward_count + 1):
                purchases = purchase_count.get(reward_id, 0)
                if purchases == 0:
                    continue
                try:
                    name, cost = self.core.functions.getReward(reward_id).call()
                except Exception:
                    name = f"Reward #{reward_id}"
                    cost = purchase_costs.get(reward_id, "?")
                rows.append((reward_id, name, cost, purchases))

            rows.sort(key=lambda item: item[3], reverse=True)
            self.popular_report_rows = []
            for rank, (_, name, cost, count) in enumerate(rows, start=1):
                self.popular_report_rows.append({
                    "Rank": rank,
                    "Reward Name": name,
                    "Cost": f"{cost} RPC",
                    "Purchases": count,
                })
                self.popular_tree.insert(
                    "", "end",
                    values=(rank, name, f"{cost} RPC", count)
                )

            total_purchases = sum(purchase_count.values())
            self._log(f"[REPORT] Popular rewards report scanned {latest + 1} blocks; "
                      f"{total_purchases} purchases found.")
        except Exception as exc:
            messagebox.showerror("History Report Error", str(exc))

    def _build_balance_snapshot(self):
        latest = self.w3.eth.block_number
        all_addresses = set()

        for block_num in range(0, latest + 1):
            block = self.w3.eth.get_block(block_num, full_transactions=True)
            for tx in block.transactions:
                all_addresses.add(tx["from"])
                if tx["to"]:
                    all_addresses.add(tx["to"])

        for acc in self.w3.eth.accounts:
            all_addresses.add(acc)

        snapshot = []
        for addr in sorted(all_addresses, key=lambda item: item.lower()):
            try:
                checksum_addr = self.w3.to_checksum_address(addr)
                rpc_balance = self.coin.functions.balanceOf(checksum_addr).call()
                eth_balance = float(self.w3.from_wei(
                    self.w3.eth.get_balance(checksum_addr), "ether"
                ))
                snapshot.append({
                    "Account Address": checksum_addr,
                    "Reward Point Coin Balance": rpc_balance,
                    "ETH Balance": round(eth_balance, 6),
                })
            except Exception:
                continue

        return snapshot

    def _export_balance_snapshot(self):
        try:
            snapshot = self._build_balance_snapshot()
            if not snapshot:
                messagebox.showwarning("No Data", "No accounts found on the blockchain.")
                return

            output_path = filedialog.asksaveasfilename(
                title="Save Balance Snapshot",
                defaultextension=".csv",
                initialfile="balance_snapshot.csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if not output_path:
                return

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "Account Address",
                        "Reward Point Coin Balance",
                        "ETH Balance",
                    ]
                )
                writer.writeheader()
                writer.writerows(snapshot)

            self._log(f"[EXPORT] Balance snapshot saved to {output_path}")
            self.status_var.set(f"Balance snapshot exported: {len(snapshot)} accounts")
            messagebox.showinfo(
                "Export Complete",
                f"Balance snapshot saved to:\n{output_path}\n\nAccounts: {len(snapshot)}"
            )
        except Exception as exc:
            messagebox.showerror("Snapshot Export Failed", str(exc))

    def _export_popular_rewards(self):
        try:
            if not self.popular_report_rows:
                self._refresh_popular_rewards()

            if not self.popular_report_rows:
                messagebox.showwarning("No Data", "No popular rewards report data to export.")
                return

            output_path = filedialog.asksaveasfilename(
                title="Save Popular Rewards Report",
                defaultextension=".csv",
                initialfile="popular_rewards_report.csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if not output_path:
                return

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["Rank", "Reward Name", "Cost", "Purchases"]
                )
                writer.writeheader()
                writer.writerows(self.popular_report_rows)

            self._log(f"[EXPORT] Popular rewards report saved to {output_path}")
            self.status_var.set("Popular rewards report exported")
            messagebox.showinfo("Export Complete", f"Report saved to:\n{output_path}")
        except Exception as exc:
            messagebox.showerror("Export Failed", str(exc))

    def _popular_report_as_text(self):
        lines = [
            "DATA HISTORY REPORT - MOST POPULAR REWARD ITEMS",
            "-" * 72,
            f"{'Rank':<6} {'Reward Name':<32} {'Cost':<14} {'Purchases':<10}",
            "-" * 72,
        ]
        for row in self.popular_report_rows:
            lines.append(
                f"{row['Rank']:<6} "
                f"{row['Reward Name']:<32} "
                f"{row['Cost']:<14} "
                f"{row['Purchases']:<10}"
            )
        return "\n".join(lines)

    def _print_popular_rewards(self):
        try:
            if not self.popular_report_rows:
                self._refresh_popular_rewards()

            if not self.popular_report_rows:
                messagebox.showwarning("No Data", "No popular rewards report data to print.")
                return

            report = self._popular_report_as_text()
            print("\n" + report + "\n")

            self.system_text.configure(state="normal")
            self.system_text.insert("end", "\n\n" + report)
            self.system_text.see("end")
            self.system_text.configure(state="disabled")

            self._log("[REPORT] Printed popular rewards text table.")
            self.status_var.set("Popular rewards report printed")
        except Exception as exc:
            messagebox.showerror("Print Failed", str(exc))

    def _selected_reward_id(self):
        sel = self.rewards_tree.selection()
        if not sel:
            raise ValueError("Select a reward from the table first")
        return int(self.rewards_tree.item(sel[0], "values")[0])

    # ─── User actions ─────────────────────────────────────────────────────────
    def _register_current_user(self):
        name = self.register_name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "Enter a name first")
            return
        try:
            acc = self._selected_account()
            tx  = self.core.functions.registerUser(name).transact({"from": acc, "gas": 200000})
            receipt = self.client.wait(tx)
            self._log(f"[REG] Registered {acc[:20]}… as '{name}'. TX: {receipt.transactionHash.hex()[:20]}…")
            self.refresh_profile()
        except Exception as exc:
            messagebox.showerror("Register Failed", str(exc))

    def _show_my_balance(self):
        self.balance_address_var.set(self._selected_account())
        self._check_address_balance()

    def _check_address_balance(self):
        try:
            addr = self.w3.to_checksum_address(self.balance_address_var.get().strip())
            rpc  = self.coin.functions.balanceOf(addr).call()
            eth  = float(self.w3.from_wei(self.w3.eth.get_balance(addr), "ether"))
            self.balance_result_var.set(f"{rpc} RPC  |  {eth:.4f} ETH")
        except Exception as exc:
            messagebox.showerror("Balance Error", str(exc))

    def _buy_selected_reward(self):
        acc = self._selected_account()
        try:
            rid       = self._selected_reward_id()
            name, cost = self.core.functions.getReward(rid).call()
            balance   = self.coin.functions.balanceOf(acc).call()
            if balance < cost:
                messagebox.showwarning("Insufficient Coins",
                    f"You have {balance} RPC.\nThis reward costs {cost} RPC.")
                return
            if not messagebox.askyesno("Confirm Purchase",
                    f"Buy '{name}' for {cost} RPC?"):
                return
            self.status_var.set(f"Processing purchase of {name}…")
            self.root.update_idletasks()
            approve_tx = self.coin.functions.approve(self.core.address, cost).transact(
                {"from": acc, "gas": 100000})
            self.client.wait(approve_tx)
            buy_tx  = self.core.functions.buyReward(rid).transact({"from": acc, "gas": 200000})
            receipt = self.client.wait(buy_tx)
            self._log(f"[BUY] Bought '{name}' for {cost} RPC. TX: {receipt.transactionHash.hex()[:20]}…")
            self.status_var.set(f"✓ Purchased '{name}' for {cost} RPC")
            self.refresh_all()
            messagebox.showinfo("Purchase Complete", f"✓  Bought '{name}' for {cost} RPC")
        except Exception as exc:
            messagebox.showerror("Purchase Failed", str(exc))

    def _transfer_coins(self):
        acc = self._selected_account()
        try:
            to_addr = self.w3.to_checksum_address(self.transfer_to_var.get().strip())
            amount  = int(self.transfer_amount_var.get().strip())
            tx      = self.coin.functions.transfer(to_addr, amount).transact(
                {"from": acc, "gas": 200000})
            receipt = self.client.wait(tx)
            self._log(f"[XFER] Sent {amount} RPC → {to_addr[:20]}…. TX: {receipt.transactionHash.hex()[:20]}…")
            self.status_var.set(f"✓ Transferred {amount} RPC")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Transfer Failed", str(exc))

    def _load_history(self):
        try:
            address = self.w3.to_checksum_address(self.history_address_var.get().strip())
        except Exception as exc:
            messagebox.showerror("Invalid Address", str(exc))
            return

        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        try:
            latest = self.w3.eth.block_number
            rows   = []
            zero   = "0x0000000000000000000000000000000000000000"

            for block_num in range(0, latest + 1):
                block = self.w3.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions:
                    tx_to    = tx["to"]
                    tx_from  = tx["from"]
                    eth_val  = float(self.w3.from_wei(tx["value"], "ether"))
                    matched  = False
                    purch    = False

                    if tx_to and tx_to.lower() in [
                        self.core.address.lower(), self.coin.address.lower()
                    ]:
                        receipt = self.w3.eth.get_transaction_receipt(tx.hash)

                        for evt in self.core.events.UserRegistered().process_receipt(
                                receipt, errors=DISCARD):
                            if evt["args"]["user"].lower() == address.lower():
                                rows.append((block_num, "Registered", "—", f"{eth_val:.4f}"))
                                matched = True

                        for evt in self.core.events.RewardPurchased().process_receipt(
                                receipt, errors=DISCARD):
                            if evt["args"]["user"].lower() == address.lower():
                                rows.append((block_num, "Buy Reward",
                                             f"-{evt['args']['cost']} RPC", f"{eth_val:.4f}"))
                                matched = purch = True

                        if not purch:
                            for evt in self.coin.events.Transfer().process_receipt(
                                    receipt, errors=DISCARD):
                                frm = evt["args"]["from"]
                                to  = evt["args"]["to"]
                                amt = evt["args"]["amount"]
                                if to.lower() == address.lower():
                                    action = "Minted" if frm.lower() == zero else "Received"
                                    rows.append((block_num, action, f"+{amt} RPC", f"{eth_val:.4f}"))
                                    matched = True
                                elif frm.lower() == address.lower():
                                    rows.append((block_num, "Sent Coins",
                                                 f"-{amt} RPC", f"{eth_val:.4f}"))
                                    matched = True

                            for evt in self.coin.events.Approval().process_receipt(
                                    receipt, errors=DISCARD):
                                if evt["args"]["owner"].lower() == address.lower():
                                    rows.append((block_num, "Approved",
                                                 f"{evt['args']['amount']} RPC", f"{eth_val:.4f}"))
                                    matched = True

                    if not matched and (
                        tx_from.lower() == address.lower()
                        or (tx_to and tx_to.lower() == address.lower())
                    ):
                        if eth_val > 0:
                            action = "ETH Out" if tx_from.lower() == address.lower() else "ETH In"
                        elif tx_to and tx_to.lower() == self.core.address.lower():
                            action = "Core Call"
                        elif tx_to and tx_to.lower() == self.coin.address.lower():
                            action = "Coin Call"
                        else:
                            action = "TX"
                        rows.append((block_num, action, "—", f"{eth_val:.4f}"))

            for row in rows:
                self.history_tree.insert("", "end", values=row)
            self._log(f"[HIST] Loaded {len(rows)} rows for {address[:20]}…")
            self.status_var.set(f"{len(rows)} history rows loaded")
        except Exception as exc:
            messagebox.showerror("History Error", str(exc))

    # ─── Admin actions ────────────────────────────────────────────────────────
    def _unlock_admin(self):
        acc      = self._selected_account()
        password = self.admin_password_var.get().strip()
        try:
            cur_admin = self.core.functions.getAdmin().call()
            if password != ADMIN_PASSWORD:
                self.admin_unlocked = False
                self._admin_led.config(text="  ●  WRONG PASSWORD", fg=ACCENT_R)
                messagebox.showerror("Access Denied", "Wrong admin password")
                return
            if acc.lower() != cur_admin.lower():
                self.admin_unlocked = False
                self._admin_led.config(text="  ●  NOT ADMIN ACCOUNT", fg=ACCENT_R)
                messagebox.showerror("Access Denied", "Selected account is not the admin")
                return
            self.admin_unlocked = True
            self._admin_led.config(text=f"  ●  UNLOCKED  ({acc[:16]}…)", fg=ACCENT_G)
            self._log(f"[AUTH] Admin unlocked as {acc[:20]}…")
            self.status_var.set("Admin panel unlocked")
        except Exception as exc:
            messagebox.showerror("Admin Error", str(exc))

    def _require_admin(self):
        if not self.admin_unlocked:
            raise PermissionError("Unlock the admin panel first")
        acc       = self._selected_account()
        cur_admin = self.core.functions.getAdmin().call()
        if acc.lower() != cur_admin.lower():
            self.admin_unlocked = False
            self._admin_led.config(text="  ●  LOCKED", fg=ACCENT_R)
            raise PermissionError("Selected account is no longer the admin")
        return acc

    def _admin_add_reward(self):
        try:
            sender = self._require_admin()
            name   = self.admin_reward_name_var.get().strip()
            cost   = int(self.admin_reward_cost_var.get().strip())
            tx     = self.core.functions.addReward(name, cost).transact({"from": sender, "gas": 200000})
            r      = self.client.wait(tx)
            self._log(f"[ADMIN] Added reward '{name}' cost={cost}. TX: {r.transactionHash.hex()[:20]}…")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Add Reward Failed", str(exc))

    def _admin_update_selected_reward(self):
        try:
            sender = self._require_admin()
            rid    = self._selected_reward_id()
            name   = self.admin_reward_name_var.get().strip()
            cost   = int(self.admin_reward_cost_var.get().strip())
            tx     = self.core.functions.updateReward(rid, name, cost).transact(
                {"from": sender, "gas": 200000})
            r = self.client.wait(tx)
            self._log(f"[ADMIN] Updated reward #{rid}. TX: {r.transactionHash.hex()[:20]}…")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Update Reward Failed", str(exc))

    def _admin_batch_add(self):
        try:
            sender = self._require_admin()
            names, costs = [], []
            for line in self.batch_add_text.get("1.0", "end").splitlines():
                line = line.strip()
                if not line:
                    continue
                name, cost = [p.strip() for p in line.split(",", 1)]
                names.append(name)
                costs.append(int(cost))
            if not names:
                raise ValueError("Enter at least one line")
            tx = self.core.functions.batchAddRewards(names, costs).transact(
                {"from": sender, "gas": 600000})
            r = self.client.wait(tx)
            self._log(f"[ADMIN] Batch added {len(names)} rewards. TX: {r.transactionHash.hex()[:20]}…")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Batch Add Failed", str(exc))

    def _admin_batch_update(self):
        try:
            sender = self._require_admin()
            ids, names, costs = [], [], []
            for line in self.batch_update_text.get("1.0", "end").splitlines():
                line = line.strip()
                if not line:
                    continue
                raw_id, name, cost = [p.strip() for p in line.split(",", 2)]
                ids.append(int(raw_id))
                names.append(name)
                costs.append(int(cost))
            if not ids:
                raise ValueError("Enter at least one line")
            tx = self.core.functions.batchUpdateRewards(ids, names, costs).transact(
                {"from": sender, "gas": 700000})
            r = self.client.wait(tx)
            self._log(f"[ADMIN] Batch updated {len(ids)} rewards. TX: {r.transactionHash.hex()[:20]}…")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Batch Update Failed", str(exc))

    def _admin_give_coins(self):
        try:
            sender    = self._require_admin()
            to_addr   = self.w3.to_checksum_address(self.mint_to_var.get().strip())
            amount    = int(self.mint_amount_var.get().strip())
            tx        = self.coin.functions.mint(to_addr, amount).transact(
                {"from": sender, "gas": 300000})
            r = self.client.wait(tx)
            self._log(f"[ADMIN] Minted {amount} RPC → {to_addr[:20]}…. TX: {r.transactionHash.hex()[:20]}…")
            self.status_var.set(f"✓ Gave {amount} RPC to {to_addr[:16]}…")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Give Coins Failed", str(exc))

    def _admin_pause(self):
        try:
            sender = self._require_admin()
            if not messagebox.askyesno("Confirm Pause", "Pause the contract?"):
                return
            tx = self.core.functions.pause().transact({"from": sender, "gas": 100000})
            r  = self.client.wait(tx)
            self._log(f"[ADMIN] Contract PAUSED. TX: {r.transactionHash.hex()[:20]}…")
            self.status_var.set("⚠ Contract paused")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Pause Failed", str(exc))

    def _admin_resume(self):
        try:
            sender = self._require_admin()
            tx = self.core.functions.resume().transact({"from": sender, "gas": 100000})
            r  = self.client.wait(tx)
            self._log(f"[ADMIN] Contract RESUMED. TX: {r.transactionHash.hex()[:20]}…")
            self.status_var.set("✓ Contract resumed")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Resume Failed", str(exc))

    def _admin_transfer_ownership(self):
        try:
            sender    = self._require_admin()
            new_admin = self.w3.to_checksum_address(self.new_admin_var.get().strip())
            if not messagebox.askyesno("Confirm Transfer",
                    f"Transfer admin rights to:\n{new_admin}\n\nThis cannot be undone without the new admin's cooperation."):
                return
            tx = self.core.functions.transferOwnership(new_admin).transact(
                {"from": sender, "gas": 100000})
            r  = self.client.wait(tx)
            self.admin_unlocked = False
            self._admin_led.config(text="  ●  LOCKED  (ownership transferred)", fg=ACCENT_A)
            self._log(f"[ADMIN] Ownership → {new_admin[:20]}…. TX: {r.transactionHash.hex()[:20]}…")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Ownership Transfer Failed", str(exc))

    # ─── Log helpers ──────────────────────────────────────────────────────────
    def _log(self, message):
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}]  {message}\n"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        # Also keep old system_text for compatibility
        try:
            self.system_text.configure(state="normal")
            self.system_text.insert("end", f"\n{message}")
            self.system_text.see("end")
            self.system_text.configure(state="disabled")
        except Exception:
            pass

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    # Keep legacy alias
    def log_message(self, message):
        self._log(message)


def main():
    root = tk.Tk()
    root.configure(bg=BG_DEEP)
    try:
        root.tk.call("tk", "scaling", 1.1)
    except Exception:
        pass
    StoreRewardsGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
