ATM Authentication
DFA Simulator

1. Introduction
This project is a visual desktop application that demonstrates the concept of a Deterministic Finite
Automaton (DFA) using a simulated ATM (Automated Teller Machine) authentication and
transaction flow. Built in Python using Tkinter, NetworkX, and Matplotlib.
The application is designed as a single-file Python program, making it straightforward to run
without complex setup. Every button press on the ATM interface triggers a DFA state transition,
which is immediately reflected on a live state diagram drawn on the right side of the window.

2. What is a Deterministic Finite Automaton (DFA)?
A Deterministic Finite Automaton is a mathematical model used in computer science and formal
language theory to describe computation. It is called 'deterministic' because for any given state and
input symbol, there is exactly one possible next state, no ambiguity, no randomness.
A DFA is formally defined as a 5-tuple:
• Q — a finite set of states
• Σ (Sigma) — a finite set of input symbols called the alphabet
• δ (Delta) — the transition function: Q × Σ → Q
• q₀ — the initial/start state
• F — a set of accepting (final) states
In this simulator, the ATM session itself is the computation. Each user action (inserting a card,
entering a PIN, selecting a transaction) is an input symbol, and the ATM's current mode (idle,
authenticated, locked, etc.) is the current state. The DFA diagram on the right visualizes all states
and transitions simultaneously.

3. System Overview
The simulator runs in a single window divided into three regions:
• Left Panel — The ATM interface: screen display, numeric keypad, and action buttons.
• Right Panel — The live DFA state diagram rendered using Matplotlib embedded in
Tkinter.
• Bottom Strip — A scrollable transition log showing every state change in real time.

6. DFA States
The simulator defines 14 states, each representing a distinct phase of an ATM session:
State Description
IDLE The machine is on and waiting. No card has been
inserted yet.
CARD_INSERTED A card has been detected. The machine prepares
to accept a PIN.
PIN_ENTRY The user is actively typing their 4-digit PIN
(masked with asterisks).
VALIDATING_PIN The entered PIN is being checked against the
stored correct PIN.
AUTHENTICATED The PIN was correct. The user is now verified and
trusted.
MAIN_MENU The authenticated user sees transaction options:
Withdraw, Deposit, Balance.
WITHDRAWAL The user is entering an amount to withdraw from
their account.
DEPOSIT The user is entering an amount to deposit into
their account.
BALANCE_CHECK The machine is displaying the current account
balance.
TRANSACTION_SUCCESS A transaction was completed. The user may do
another or finish.
INVALID_PIN The entered PIN was incorrect. The user may
retry (up to 3 attempts).
3
State Description
CARD_LOCKED Three consecutive wrong PINs. The card is locked
for security.
EJECT_CARD The machine is ejecting the card, ending the
session.
EXIT The session is fully over. The machine loops back
to IDLE.
7. DFA Transition Table
The table below defines the complete transition function δ of the DFA. Each row reads: given the
current state and an input symbol, the machine moves to the next state.
Current State Input Symbol Next State
IDLE insert_card CARD_INSERTED
CARD_INSERTED start_pin PIN_ENTRY
PIN_ENTRY submit_pin VALIDATING_PIN
VALIDATING_PIN correct_pin AUTHENTICATED
VALIDATING_PIN wrong_pin INVALID_PIN
INVALID_PIN retry PIN_ENTRY
INVALID_PIN third_attempt CARD_LOCKED
CARD_LOCKED eject EJECT_CARD
AUTHENTICATED open_menu MAIN_MENU
MAIN_MENU withdraw WITHDRAWAL
MAIN_MENU deposit DEPOSIT
MAIN_MENU check_balance BALANCE_CHECK
WITHDRAWAL success TRANSACTION_SUCCESS
DEPOSIT success TRANSACTION_SUCCESS
BALANCE_CHECK success TRANSACTION_SUCCESS
4
Current State Input Symbol Next State
TRANSACTION_SUCCESS back_to_menu MAIN_MENU
TRANSACTION_SUCCESS finish EJECT_CARD
EJECT_CARD remove_card EXIT
EXIT new_session IDLE
8. Key Logic and Features
6.1 PIN Validation and Lockout
The simulator uses a fake account with PIN 1234 and a starting balance of ₱5,000. When the user
submits a PIN, the DFA moves to VALIDATING_PIN and checks the input. A correct PIN
transitions to AUTHENTICATED. An incorrect PIN moves to INVALID_PIN and increments a
counter. After three consecutive failures, the transition symbol third_attempt is used instead of
retry, sending the machine to CARD_LOCKED and then automatically to EJECT_CARD.
6.2 Transaction Loop
Once authenticated and inside MAIN_MENU, the user can perform multiple transactions. After
each successful transaction (TRANSACTION_SUCCESS), the Back to Main Menu button fires
the back_to_menu symbol, looping the DFA back to MAIN_MENU without ejecting the card.
This allows multiple operations in a single authenticated session.
6.3 Session Loop (EXIT → IDLE)
When a session ends and the machine reaches EXIT, the red circle button at the top-left of the
ATM panel fires the new_session symbol, transitioning the DFA back to IDLE. This creates a
continuous loop without requiring a full application reset, preserving the transaction log for
demonstration purposes.
6.4 Reset Simulation
The Reset Simulation button performs a hard reset: it clears the transition log, restores the balance
to ₱5,000, clears PIN attempt counters, and forces the DFA back to IDLE. It is intended for starting
a completely fresh demonstration.
9. DFA Visualisation
The right panel of the application contains a live graph rendered by Matplotlib and NetworkX. The
graph is redrawn every time a state transition occurs. The following visual conventions are used:
• Active state node — highlighted in green to show where the DFA currently is.
• Error state nodes (INVALID_PIN, CARD_LOCKED) — permanently coloured red.
5
• Active transition arrow — drawn in amber/yellow with increased thickness to show the
last transition taken.
• All other nodes and edges — drawn in dark blue-grey as default.
• A callout annotation floats above the active node displaying its name clearly.
Node positions are manually fixed in a horizontal flow layout so the diagram is always readable
and predictable during a presentation, regardless of graph library defaults.
10. Transition Log
The bottom strip of the window contains a scrollable real-time log. Every state transition appends
a new line in the format:
[IDLE] ──insert_card──> [CARD_INSERTED]
Log entries are colour-coded: green for successful transitions, red for error states, amber for
warnings, and teal for neutral informational transitions. This allows an audience to follow the
DFA's history at a glance.
11. Technology Stack
Library Role in the Project
Python Core language. All logic, state management, and event
handling.
Tkinter GUI framework. Builds the window, ATM panel, buttons,
screen, and log strip.
NetworkX Graph library. Stores the DFA as a directed graph (DiGraph)
with labelled edges.
Matplotlib Visualisation. Renders the DFA diagram inside the Tkinter
window via FigureCanvasTkAgg.

13. How to Run
Install dependencies (run once in your terminal):
pip install networkx matplotlib
Run the simulator:
python atm_dfa_simulator.py
No database, no internet connection, and no additional files are required. The entire program is
self-contained in a single .py file.
