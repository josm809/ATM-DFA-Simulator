"""
ATM Authentication DFA Simulator
=================================
atm authentication with dfa live simulation

FAKE ACCOUNT:
    PIN     = 1234
    Balance = 5000
"""

import tkinter as tk
from tkinter import font as tkfont
import networkx as nx
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math

#─────────────────────────────────────────────────────────────────
#ui colors  
#─────────────────────────────────────────────────────────────────
BG_DARK       = "#0A0E1A"   # main window background
BG_PANEL      = "#0F1629"   # panel background
BG_ATM        = "#141D35"   # ATM body
BG_SCREEN     = "#0D1F0D"   # ATM screen (green-tinted)
FG_SCREEN     = "#00FF41"   # screen text (matrix green)
FG_LABEL      = "#8892A4"   # muted label colour
FG_WHITE      = "#E8EDF5"   # bright text
ACCENT_BLUE   = "#1565C0"   # button accent
ACCENT_TEAL   = "#00BCD4"   # highlights
ACCENT_RED    = "#D32F2F"   # error / locked
ACCENT_GREEN  = "#00C853"   # success / active
ACCENT_AMBER  = "#FFB300"   # transition flash
BTN_NUM_BG    = "#1C2742"
BTN_NUM_FG    = "#E8EDF5"
BTN_NUM_ACT   = "#243456"
DIVIDER       = "#1E2A45"

#graph colours
NODE_DEFAULT  = "#1C2742"
NODE_ACTIVE   = "#00C853"
NODE_ERROR    = "#D32F2F"
NODE_LOCKED   = "#8B0000"
NODE_BORDER   = "#3A4F7A"
EDGE_DEFAULT  = "#2E4070"
EDGE_ACTIVE   = "#FFB300"
GRAPH_BG      = "#090D1A"

#─────────────────────────────────────────────────────────────────
#dfa def
# ─────────────────────────────────────────────────────────────────
#all states in the ATM DFA
DFA_STATES = [
    "IDLE", "CARD_INSERTED", "PIN_ENTRY", "VALIDATING_PIN",
    "AUTHENTICATED", "MAIN_MENU", "WITHDRAWAL", "DEPOSIT",
    "BALANCE_CHECK", "TRANSACTION_SUCCESS", "INVALID_PIN",
    "CARD_LOCKED", "EJECT_CARD", "EXIT"
]

#transitions: (from_state, symbol/action, to_state)
DFA_TRANSITIONS = [
    ("IDLE",                "insert_card",   "CARD_INSERTED"),
    ("CARD_INSERTED",       "start_pin",     "PIN_ENTRY"),
    ("PIN_ENTRY",           "submit_pin",    "VALIDATING_PIN"),
    ("VALIDATING_PIN",      "correct_pin",   "AUTHENTICATED"),
    ("VALIDATING_PIN",      "wrong_pin",     "INVALID_PIN"),
    ("INVALID_PIN",         "retry",         "PIN_ENTRY"),
    ("INVALID_PIN",         "third_attempt", "CARD_LOCKED"),
    ("CARD_LOCKED",         "eject",         "EJECT_CARD"),
    ("AUTHENTICATED",       "open_menu",     "MAIN_MENU"),
    ("MAIN_MENU",           "withdraw",      "WITHDRAWAL"),
    ("MAIN_MENU",           "deposit",       "DEPOSIT"),
    ("MAIN_MENU",           "check_balance", "BALANCE_CHECK"),
    ("WITHDRAWAL",          "success",       "TRANSACTION_SUCCESS"),
    ("DEPOSIT",             "success",       "TRANSACTION_SUCCESS"),
    ("BALANCE_CHECK",       "success",       "TRANSACTION_SUCCESS"),
    ("TRANSACTION_SUCCESS", "finish",        "EJECT_CARD"),
    ("TRANSACTION_SUCCESS", "back_to_menu",  "MAIN_MENU"),   #loop-back
    ("EJECT_CARD",          "remove_card",   "EXIT"),
    ("EXIT",                "new_session",   "IDLE"),    #loop back
]

#error/locked states get a red tint in the diagram
ERROR_STATES  = {"INVALID_PIN", "CARD_LOCKED"}
FINISH_STATES = {"EXIT"}

#─────────────────────────────────────────────────────────────────
#node positions
#─────────────────────────────────────────────────────────────────
NODE_POS = {
    "IDLE":                 (0,    5),
    "CARD_INSERTED":        (2,    5),
    "PIN_ENTRY":            (4,    5),
    "VALIDATING_PIN":       (6,    5),
    "AUTHENTICATED":        (8,    5),
    "MAIN_MENU":            (10,   5),
    "WITHDRAWAL":           (12,   7),
    "DEPOSIT":              (12,   5),
    "BALANCE_CHECK":        (12,   3),
    "TRANSACTION_SUCCESS":  (14,   5),
    "EJECT_CARD":           (16,   5),
    "EXIT":                 (18,   5),
    "INVALID_PIN":          (6,    2),
    "CARD_LOCKED":          (8,    0),
}

#─────────────────────────────────────────────────────────────────
#MAIN APPLICATION CLASS
#─────────────────────────────────────────────────────────────────
class ATMDFASimulator:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ATM Authentication — DFA Simulator")
        self.root.configure(bg=BG_DARK)
        self.root.geometry("1400x820")
        self.root.minsize(1200, 700)

        # ── Account / simulation state ──────────────────────────
        self.CORRECT_PIN    = "1234"
        self.INITIAL_BALANCE = 5000
        self.balance        = self.INITIAL_BALANCE
        self.pin_attempts   = 0
        self.pin_input      = ""        # raw digits typed
        self.amount_input   = ""        # amount for withdraw/deposit
        self.current_state  = "IDLE"
        self.prev_state     = None
        self.active_edge    = None      # (from, to) currently highlighted

        # Logs list
        self.logs: list[str] = []

        # ── Build NetworkX graph ─────────────────────────────────
        self._build_graph()

        # ── Build UI ─────────────────────────────────────────────
        self._build_ui()

        # ── Initial diagram draw ─────────────────────────────────
        self._redraw_graph()
        self._update_atm_screen("Welcome!\nPlease insert your card.")

    #─────────────────────────────────────────────────────────────
    #GRAPH CONSTRUCTION
    #─────────────────────────────────────────────────────────────
    def _build_graph(self):
        """Build a directed NetworkX graph from the DFA transition table."""
        self.G = nx.DiGraph()
        self.G.add_nodes_from(DFA_STATES)
        for (src, label, dst) in DFA_TRANSITIONS:
            # Store edge label as attribute
            self.G.add_edge(src, dst, label=label)

    #─────────────────────────────────────────────────────────────
    #UI CONSTRUCTION
    #─────────────────────────────────────────────────────────────
    def _build_ui(self):
        """Create the two-panel layout + bottom log strip."""
        # Title bar
        title_bar = tk.Frame(self.root, bg=BG_DARK, pady=6)
        title_bar.pack(fill="x")
        tk.Label(
            title_bar, text="◈  ATM Authentication — DFA Simulator  ◈",
            bg=BG_DARK, fg=ACCENT_TEAL,
            font=("Courier New", 15, "bold")
        ).pack()

        # Main content frame
        main = tk.Frame(self.root, bg=BG_DARK)
        main.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        # Left ATM panel (fixed width)
        left = tk.Frame(main, bg=BG_PANEL, width=360,
                        relief="flat", bd=0)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        self._build_atm_panel(left)

        # Right graph panel (expands)
        right = tk.Frame(main, bg=BG_PANEL, relief="flat", bd=0)
        right.pack(side="left", fill="both", expand=True)
        self._build_graph_panel(right)

        # Bottom log strip
        log_frame = tk.Frame(self.root, bg=BG_PANEL, height=130)
        log_frame.pack(fill="x", padx=10, pady=(0, 8))
        log_frame.pack_propagate(False)
        self._build_log_panel(log_frame)

    # ── ATM Panel ─────────────────────────────────────────────────
    def _build_atm_panel(self, parent):
        """Build the left ATM simulation panel."""
        # ATM body frame
        body = tk.Frame(parent, bg=BG_ATM, padx=16, pady=14)
        body.pack(fill="both", expand=True, padx=12, pady=12)

        # Brand label row with red "New Session" circle button at top-left
        brand_row = tk.Frame(body, bg=BG_ATM)
        brand_row.pack(fill="x", pady=(0, 8))

        # Red circle button — triggers EXIT → IDLE loop-back
        new_sess_btn = tk.Button(
            brand_row, text="●", command=self._new_session,
            bg=ACCENT_RED, fg=FG_WHITE,
            activebackground="#B71C1C", activeforeground=FG_WHITE,
            font=("Courier New", 13, "bold"),
            width=2, height=1,
            relief="flat", bd=0, cursor="hand2",
        )
        new_sess_btn.pack(side="left", padx=(0, 8))

        tk.Label(brand_row, text="◈ LEMOJ ATM ◈",
                 bg=BG_ATM, fg=ACCENT_TEAL,
                 font=("Courier New", 11, "bold")).pack(side="left")

        # ATM Screen
        screen_frame = tk.Frame(body, bg="#0A1A0A",
                                relief="sunken", bd=2, padx=2, pady=2)
        screen_frame.pack(fill="x", pady=(0, 12))
        self.screen_var = tk.StringVar(value="")
        self.screen_label = tk.Label(
            screen_frame, textvariable=self.screen_var,
            bg=BG_SCREEN, fg=FG_SCREEN,
            font=("Courier New", 11),
            width=28, height=6,
            anchor="nw", justify="left",
            padx=8, pady=6, wraplength=280
        )
        self.screen_label.pack()

        # PIN display row
        pin_row = tk.Frame(body, bg=BG_ATM)
        pin_row.pack(fill="x", pady=(0, 8))
        tk.Label(pin_row, text="PIN:", bg=BG_ATM, fg=FG_LABEL,
                 font=("Courier New", 10)).pack(side="left")
        self.pin_display = tk.Label(
            pin_row, text="", bg=BG_ATM, fg=FG_SCREEN,
            font=("Courier New", 14, "bold"), width=10, anchor="w"
        )
        self.pin_display.pack(side="left", padx=6)

        # State indicator
        state_row = tk.Frame(body, bg=BG_ATM)
        state_row.pack(fill="x", pady=(0, 10))
        tk.Label(state_row, text="STATE:", bg=BG_ATM, fg=FG_LABEL,
                 font=("Courier New", 9)).pack(side="left")
        self.state_label = tk.Label(
            state_row, text="IDLE",
            bg=BG_ATM, fg=ACCENT_GREEN,
            font=("Courier New", 10, "bold"), width=20, anchor="w"
        )
        self.state_label.pack(side="left", padx=4)

        # ── Numeric Keypad ────────────────────────────────────────
        kpad_frame = tk.Frame(body, bg=BG_ATM)
        kpad_frame.pack(pady=(0, 10))

        digits = [
            ("7", "8", "9"),
            ("4", "5", "6"),
            ("1", "2", "3"),
            ("",  "0", "⌫"),
        ]
        for row_digits in digits:
            row = tk.Frame(kpad_frame, bg=BG_ATM)
            row.pack()
            for d in row_digits:
                if d == "":
                    tk.Label(row, width=5, bg=BG_ATM).pack(
                        side="left", padx=3, pady=3)
                else:
                    cmd = (lambda x=d: self._keypad_press(x)) if d != "⌫" \
                          else self._keypad_backspace
                    btn = self._make_btn(row, d, cmd,
                                        bg=BTN_NUM_BG, fg=BTN_NUM_FG,
                                        w=5, h=2,
                                        font=("Courier New", 11, "bold"))
                    btn.pack(side="left", padx=3, pady=3)

        # ── Action Buttons ────────────────────────────────────────
        sep = tk.Frame(body, bg=DIVIDER, height=1)
        sep.pack(fill="x", pady=8)

        actions = [
            ("💳  Insert Card",       self._insert_card,     ACCENT_BLUE),
            ("✔  Enter / Confirm",    self._enter_pin,       "#1B5E20"),
            ("💸  Withdraw",           self._withdraw,        "#4A148C"),
            ("🏦  Deposit",            self._deposit,         "#004D40"),
            ("💰  Balance",            self._check_balance,   "#1A237E"),
            ("↩  Back to Main Menu",  self._back_to_menu,    "#0D47A1"),
            ("🔚  Finish Transaction", self._finish_txn,      "#37474F"),
            ("🔄  Reset Simulation",   self._reset,           ACCENT_RED),
        ]
        for (label, cmd, colour) in actions:
            self._make_btn(body, label, cmd,
                           bg=colour, fg=FG_WHITE,
                           w=26, h=2,
                           font=("Courier New", 10, "bold")
                           ).pack(pady=2, fill="x")

    # ── Graph Panel ───────────────────────────────────────────────
    def _build_graph_panel(self, parent):
        tk.Label(parent, text="DFA State Diagram  (live)",
                 bg=BG_PANEL, fg=ACCENT_TEAL,
                 font=("Courier New", 11, "bold")).pack(pady=(8, 4))

        self.fig, self.ax = plt.subplots(figsize=(10, 5.6))
        self.fig.patch.set_facecolor(GRAPH_BG)
        self.ax.set_facecolor(GRAPH_BG)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True,
                                         padx=8, pady=(0, 8))

    # ── Log Panel ─────────────────────────────────────────────────
    def _build_log_panel(self, parent):
        hdr = tk.Frame(parent, bg=BG_PANEL)
        hdr.pack(fill="x", padx=10, pady=(6, 0))
        tk.Label(hdr, text="▶  Transition Log",
                 bg=BG_PANEL, fg=ACCENT_TEAL,
                 font=("Courier New", 10, "bold")).pack(side="left")

        log_body = tk.Frame(parent, bg=BG_PANEL)
        log_body.pack(fill="both", expand=True, padx=10, pady=(2, 6))

        scrollbar = tk.Scrollbar(log_body)
        scrollbar.pack(side="right", fill="y")

        self.log_text = tk.Text(
            log_body, bg="#060A14", fg=ACCENT_GREEN,
            font=("Courier New", 9),
            state="disabled", bd=0,
            yscrollcommand=scrollbar.set,
            wrap="word", height=5
        )
        self.log_text.pack(fill="both", expand=True)
        scrollbar.config(command=self.log_text.yview)

        self.log_text.tag_configure("error",   foreground=ACCENT_RED)
        self.log_text.tag_configure("success", foreground=ACCENT_GREEN)
        self.log_text.tag_configure("info",    foreground=ACCENT_TEAL)
        self.log_text.tag_configure("warn",    foreground=ACCENT_AMBER)

    # ─────────────────────────────────────────────────────────────
    #  HELPER: button factory
    # ─────────────────────────────────────────────────────────────
    def _make_btn(self, parent, text, command,
                  bg="#1C2742", fg="#E8EDF5",
                  w=6, h=2,
                  font=("Courier New", 10, "bold")):
        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg,
            activebackground=BTN_NUM_ACT, activeforeground=FG_WHITE,
            font=font, width=w, height=h,
            relief="flat", bd=0, cursor="hand2"
        )
        return btn

    # ─────────────────────────────────────────────────────────────
    #  DFA TRANSITION ENGINE
    # ─────────────────────────────────────────────────────────────
    def _transition(self, symbol: str) -> bool:
        """
        Attempt a DFA transition from current_state via symbol.
        Returns True if a valid transition was found.
        Logs the result and triggers graph update.
        """
        src = self.current_state
        for (s, sym, dst) in DFA_TRANSITIONS:
            if s == src and sym == symbol:
                # Valid transition found
                self.prev_state   = src
                self.current_state = dst
                self.active_edge  = (src, dst)

                tag = "error" if dst in ERROR_STATES else \
                      "success" if dst in {"AUTHENTICATED",
                                           "TRANSACTION_SUCCESS",
                                           "EXIT"} else "info"
                self._log(f"[{src}]  ──{symbol}──▶  [{dst}]", tag=tag)
                self.state_label.config(text=dst,
                    fg=ACCENT_RED if dst in ERROR_STATES else ACCENT_GREEN)
                self._redraw_graph()
                return True

        # No valid transition
        self._log(f"✗ No transition from [{src}] via '{symbol}'",
                  tag="warn")
        return False

    # ─────────────────────────────────────────────────────────────
    #  DFA GRAPH DRAWING
    # ─────────────────────────────────────────────────────────────
    def _redraw_graph(self):
        """
        - Active state → green node
        - Error states → red nodes
        - Active transition edge → amber / yellow
        - All others → default blue-grey
        """
        self.ax.clear()
        self.ax.set_facecolor(GRAPH_BG)
        self.ax.axis("off")

        G   = self.G
        pos = NODE_POS

        # ── Node colours ────────────────────────────────────────
        node_colors  = []
        node_borders = []
        for n in G.nodes():
            if n == self.current_state:
                node_colors.append(NODE_ACTIVE)
                node_borders.append(ACCENT_GREEN)
            elif n in ERROR_STATES:
                node_colors.append(NODE_ERROR)
                node_borders.append(ACCENT_RED)
            elif n == "EXIT":
                node_colors.append("#1A2A1A")
                node_borders.append(ACCENT_GREEN)
            elif n == "CARD_LOCKED":
                node_colors.append(NODE_LOCKED)
                node_borders.append(ACCENT_RED)
            else:
                node_colors.append(NODE_DEFAULT)
                node_borders.append(NODE_BORDER)

        # ── Edge colours ─────────────────────────────────────────
        edge_colors = []
        edge_widths = []
        for (u, v) in G.edges():
            if self.active_edge and (u, v) == self.active_edge:
                edge_colors.append(EDGE_ACTIVE)
                edge_widths.append(3.5)
            else:
                edge_colors.append(EDGE_DEFAULT)
                edge_widths.append(1.2)

        # Curved connection style for overlapping edges
        connection_style = "arc3,rad=0.15"

        # ── Draw edges ───────────────────────────────────────────
        nx.draw_networkx_edges(
            G, pos, ax=self.ax,
            edge_color=edge_colors,
            width=edge_widths,
            arrows=True,
            arrowstyle="-|>",
            arrowsize=20,
            connectionstyle=connection_style,
            min_source_margin=22,
            min_target_margin=22,
        )

        # ── Draw nodes ───────────────────────────────────────────
        nx.draw_networkx_nodes(
            G, pos, ax=self.ax,
            node_color=node_colors,
            node_size=1400,
            linewidths=2.5,
            edgecolors=node_borders,
        )

        # ── Draw node labels (split long names across two lines) ─
        short = {
            n: n.replace("_", "\n") for n in G.nodes()
        }
        nx.draw_networkx_labels(
            G, pos, labels=short, ax=self.ax,
            font_color=FG_WHITE,
            font_size=5.5,
            font_family="monospace",
        )

        # ── Draw edge labels ──────────────────────────────────────
        edge_labels = {
            (u, v): d["label"].replace("_", "\n")
            for u, v, d in G.edges(data=True)
        }
        nx.draw_networkx_edge_labels(
            G, pos, edge_labels=edge_labels, ax=self.ax,
            font_size=5,
            font_color=ACCENT_AMBER,
            font_family="monospace",
            bbox=dict(boxstyle="round,pad=0.15",
                      fc=GRAPH_BG, ec="none", alpha=0.75),
            label_pos=0.35,
        )

        # ── Current-state callout ────────────────────────────────
        cs = self.current_state
        x, y = pos[cs]
        self.ax.annotate(
            f" ► {cs} ",
            xy=(x, y), xytext=(x, y + 1.05),
            fontsize=7, color=ACCENT_GREEN,
            fontfamily="monospace",
            ha="center",
            bbox=dict(boxstyle="round,pad=0.3",
                      fc="#001A00", ec=ACCENT_GREEN, lw=1.2),
            arrowprops=dict(arrowstyle="-", color=ACCENT_GREEN,
                            lw=0.8),
        )

        self.ax.set_xlim(-1, 20)
        self.ax.set_ylim(-1.5, 7.5)
        self.fig.tight_layout(pad=0.3)
        self.canvas.draw()

    # ─────────────────────────────────────────────────────────────
    #  LOG HELPERS
    # ─────────────────────────────────────────────────────────────
    def _log(self, message: str, tag: str = "info"):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        self.logs.append(message)

    def _update_atm_screen(self, text: str):
        self.screen_var.set(text)

    # ─────────────────────────────────────────────────────────────
    #  KEYPAD INPUT
    # ─────────────────────────────────────────────────────────────
    def _keypad_press(self, digit: str):
        if self.current_state == "PIN_ENTRY":
            if len(self.pin_input) < 4:
                self.pin_input += digit
                self.pin_display.config(text="*" * len(self.pin_input))
                self._update_atm_screen(
                    f"Enter PIN:\n{'*' * len(self.pin_input)}\n"
                    f"({len(self.pin_input)}/4 digits)"
                )

        elif self.current_state in {"WITHDRAWAL", "DEPOSIT"}:
            self.amount_input += digit
            action = "Withdraw" if self.current_state == "WITHDRAWAL" else "Deposit"
            self._update_atm_screen(
                f"{action} amount:\n₱ {self.amount_input}\n\nPress ENTER to confirm."
            )

    def _keypad_backspace(self):
        if self.current_state == "PIN_ENTRY" and self.pin_input:
            self.pin_input = self.pin_input[:-1]
            self.pin_display.config(text="*" * len(self.pin_input))

    # ─────────────────────────────────────────────────────────────
    #  ATM ACTION HANDLERS (each maps to a DFA transition symbol)
    # ─────────────────────────────────────────────────────────────

    # 1. INSERT CARD ─────────────────────────────────────────────
    def _insert_card(self):
        if self.current_state != "IDLE":
            self._update_atm_screen("⚠  Card already inserted\nor simulation in progress.")
            return
        self._transition("insert_card")
        # Auto-advance: CARD_INSERTED → PIN_ENTRY (start_pin)
        self.root.after(600, self._auto_start_pin)

    def _auto_start_pin(self):
        if self.current_state == "CARD_INSERTED":
            self._transition("start_pin")
            self._update_atm_screen(
                "Card accepted.\n\nPlease enter your\n4-digit PIN:")
            self.pin_input = ""
            self.pin_display.config(text="")

    # 2. ENTER / CONFIRM PIN ──────────────────────────────────────
    def _enter_pin(self):
        s = self.current_state

        # Submit PIN from PIN_ENTRY
        if s == "PIN_ENTRY":
            if len(self.pin_input) != 4:
                self._update_atm_screen("⚠  Please enter\nall 4 PIN digits.")
                return
            self._transition("submit_pin")
            self.root.after(500, self._validate_pin)

        # Confirm withdrawal / deposit amount
        elif s == "WITHDRAWAL":
            self._process_withdrawal()
        elif s == "DEPOSIT":
            self._process_deposit()
        else:
            self._update_atm_screen("⚠  Nothing to confirm\nin current state.")

    def _validate_pin(self):
        """DFA: VALIDATING_PIN → correct_pin / wrong_pin."""
        if self.pin_input == self.CORRECT_PIN:
            self.pin_attempts = 0
            self._transition("correct_pin")
            self._update_atm_screen("✔  PIN Accepted!\n\nWelcome back.")
            self.root.after(700, self._open_menu)
        else:
            self.pin_attempts += 1
            if self.pin_attempts >= 3:
                self._transition("wrong_pin")
                self._update_atm_screen(
                    "✘  Wrong PIN.\nThird attempt!\nCard will be locked.")
                self.root.after(800, self._lock_card)
            else:
                remaining = 3 - self.pin_attempts
                self._transition("wrong_pin")
                self._update_atm_screen(
                    f"✘  Wrong PIN.\n{remaining} attempt(s) remaining.\n"
                    f"Press Insert Card to retry.")
                self.root.after(700, self._retry_pin)

    def _retry_pin(self):
        """DFA: INVALID_PIN → retry → PIN_ENTRY."""
        self._transition("retry")
        self.pin_input = ""
        self.pin_display.config(text="")
        self._update_atm_screen(
            f"Re-enter PIN:\n\nAttempt {self.pin_attempts + 1} of 3")

    def _lock_card(self):
        """DFA: INVALID_PIN → third_attempt → CARD_LOCKED → eject → EJECT_CARD."""
        self._transition("third_attempt")
        self._update_atm_screen(
            "🔒  CARD LOCKED!\nToo many wrong attempts.\nPlease contact your bank.")
        self.root.after(900, self._eject_locked)

    def _eject_locked(self):
        self._transition("eject")
        self._update_atm_screen(
            "⏏  Please collect\nyour card.\n\nSession ended.")
        # Auto-advance: EJECT_CARD → EXIT after a short delay
        self.root.after(1200, self._remove_card)

    # 3. OPEN MAIN MENU ──────────────────────────────────────────
    def _open_menu(self):
        if self.current_state == "AUTHENTICATED":
            self._transition("open_menu")
            self._update_atm_screen(
                "MAIN MENU\n\n"
                "[Withdraw]  [Deposit]\n"
                "[Balance]   [Finish]"
            )

    # 4. WITHDRAW ────────────────────────────────────────────────
    def _withdraw(self):
        if self.current_state != "MAIN_MENU":
            self._update_atm_screen("⚠  Go to Main Menu first.")
            return
        self._transition("withdraw")
        self.amount_input = ""
        self._update_atm_screen(
            "WITHDRAWAL\n\nEnter amount (₱):\n\nUse keypad, then ENTER.")

    def _process_withdrawal(self):
        if not self.amount_input:
            self._update_atm_screen("⚠  Enter an amount\nusing the keypad.")
            return
        amt = int(self.amount_input)
        if amt <= 0:
            self._update_atm_screen("⚠  Amount must be\ngreater than ₱0.")
            return
        if amt > self.balance:
            self._update_atm_screen(
                f"✘  Insufficient funds!\nBalance: ₱{self.balance:,}\n"
                f"Requested: ₱{amt:,}")
            self.amount_input = ""
            return
        self.balance -= amt
        self._transition("success")
        self._update_atm_screen(
            f"✔  Withdrawal Success!\n\n₱{amt:,} dispensed.\n"
            f"Balance: ₱{self.balance:,}")

    # 5. DEPOSIT ─────────────────────────────────────────────────
    def _deposit(self):
        if self.current_state != "MAIN_MENU":
            self._update_atm_screen("⚠  Go to Main Menu first.")
            return
        self._transition("deposit")
        self.amount_input = ""
        self._update_atm_screen(
            "DEPOSIT\n\nEnter amount (₱):\n\nUse keypad, then ENTER.")

    def _process_deposit(self):
        if not self.amount_input:
            self._update_atm_screen("⚠  Enter an amount\nusing the keypad.")
            return
        amt = int(self.amount_input)
        if amt <= 0:
            self._update_atm_screen("⚠  Amount must be\ngreater than ₱0.")
            return
        self.balance += amt
        self._transition("success")
        self._update_atm_screen(
            f"✔  Deposit Success!\n\n₱{amt:,} credited.\n"
            f"Balance: ₱{self.balance:,}")

    # 6. BALANCE CHECK ────────────────────────────────────────────
    def _check_balance(self):
        if self.current_state != "MAIN_MENU":
            self._update_atm_screen("⚠  Go to Main Menu first.")
            return
        self._transition("check_balance")
        self._update_atm_screen(
            f"BALANCE ENQUIRY\n\n"
            f"Available Balance:\n\n  ₱ {self.balance:,.2f}")
        self.root.after(400, self._auto_success)

    def _auto_success(self):
        """Balance check auto-transitions to TRANSACTION_SUCCESS."""
        if self.current_state == "BALANCE_CHECK":
            self._transition("success")

    # 6a. NEW SESSION (EXIT → IDLE loop-back) ────────────────────
    def _new_session(self):
        """DFA: EXIT → new_session → IDLE. Loops the machine back to start."""
        if self.current_state != "EXIT":
            self._update_atm_screen(
                "⚠  Only available after\n"
                "session has fully ended.")
            return
        self.pin_attempts  = 0
        self.pin_input     = ""
        self.amount_input  = ""
        self.active_edge   = None
        self.pin_display.config(text="")
        self._transition("new_session")
        self.state_label.config(text="IDLE", fg=ACCENT_GREEN)
        self._update_atm_screen("Welcome!\nPlease insert your card.")

    # 6b. BACK TO MAIN MENU ─────────────────────────────────────
    def _back_to_menu(self):
        """DFA: TRANSACTION_SUCCESS → back_to_menu → MAIN_MENU."""
        if self.current_state != "TRANSACTION_SUCCESS":
            self._update_atm_screen(
                "⚠  Only available after\n"
                "a completed transaction.")
            return
        self._transition("back_to_menu")
        self._update_atm_screen(
            "MAIN MENU\n\n"
            "[Withdraw]  [Deposit]\n"
            "[Balance]   [Finish]"
        )

    # 7. FINISH TRANSACTION ──────────────────────────────────────
    def _finish_txn(self):
        if self.current_state == "EJECT_CARD":
            # Card already ejected (e.g. lock path) — just do remove_card
            self._remove_card()
        elif self.current_state == "TRANSACTION_SUCCESS":
            self._transition("finish")
            self._update_atm_screen(
                "⏏  Please collect\nyour card.\n\nThank you!")
            self.root.after(800, self._remove_card)
        elif self.current_state == "MAIN_MENU":
            # User wants to leave without transacting
            self._log("Manually finishing from MAIN_MENU — forcing TRANSACTION_SUCCESS path",
                      tag="warn")
            self._transition("withdraw")      # dummy path: withdraw → success
            self.root.after(100, lambda: self._transition("success"))
            self.root.after(700, lambda: self._transition("finish"))
            self.root.after(1400, self._remove_card)
            self._update_atm_screen("⏏  Session ending...\nPlease collect your card.")
        else:
            self._update_atm_screen("⚠  Complete or cancel\ncurrent transaction first.")

    def _remove_card(self):
        # Guard: only fire the DFA transition once while in EJECT_CARD
        if self.current_state == "EJECT_CARD":
            self._transition("remove_card")
            self._update_atm_screen(
                "✔  Session complete.\nCard removed.\n\nGoodbye!\n\n"
                "Press [New Session] to\nstart again.")

    # 8. RESET ────────────────────────────────────────────────────
    def _reset(self):
        """Reset ALL state back to the initial IDLE condition."""
        self.current_state  = "IDLE"
        self.prev_state     = None
        self.active_edge    = None
        self.balance        = self.INITIAL_BALANCE
        self.pin_attempts   = 0
        self.pin_input      = ""
        self.amount_input   = ""
        self.logs           = []

        # Clear log panel
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

        # Reset UI labels
        self.pin_display.config(text="")
        self.state_label.config(text="IDLE", fg=ACCENT_GREEN)
        self._update_atm_screen("Simulation reset.\n\nWelcome!\nPlease insert your card.")
        self._log("── Simulation Reset ──", tag="warn")
        self._redraw_graph()


# ─────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = ATMDFASimulator(root)
    root.mainloop()
