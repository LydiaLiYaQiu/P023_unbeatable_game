# -*- coding: utf-8 -*-
"""
P023 "Can You Build an Unbeatable Game?" — Task 1
Analysis of winning (N) and losing (P) positions for three impartial games.

Games analysed:
  1. Subtraction game (single heap, remove 1..k)
  2. Nim (two heaps)
  3. Wythoff's game (two heaps)

Method (backward induction, the "experiment"):
  * A position is P ("Previous player wins", i.e. LOSING for the player about
    to move) iff EVERY legal move leads to an N-position.
  * A position is N ("Next player wins", WINNING) iff SOME legal move leads to
    a P-position.
  * The terminal position (no legal move) is P.

Each brute-force enumeration is then checked against the closed-form theory.

Outputs:
  * results.txt  — verification report + lists of P-positions
  * figs/*.png   — P/N position diagrams
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap

# ----------------------------------------------------------------------------
# Palette (validated reference instance)
# ----------------------------------------------------------------------------
P_COLOR = "#2a78d6"   # blue   = P-position (losing for the mover)
N_COLOR = "#eb6834"   # orange = N-position (winning for the mover)
SURFACE = "#fcfcfb"
CELL_GAP = "#ffffff"
INK     = "#0b0b0b"
SECONDARY = "#52514e"
REF_LINE = "#c3c2b7"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": SECONDARY,
    "ytick.color": SECONDARY,
    "axes.edgecolor": REF_LINE,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


# ----------------------------------------------------------------------------
# 1. Subtraction game
# ----------------------------------------------------------------------------
def subtraction_positions(k, N):
    """Return P[0..N], P[n] == True iff n is a P-position (losing)."""
    P = [None] * (N + 1)
    P[0] = True  # no tokens left -> mover has no move -> P
    for n in range(1, N + 1):
        # n is P iff every legal move n -> n-x lands on an N-position
        P[n] = all(not P[n - x] for x in range(1, min(k, n) + 1))
    return P


# ----------------------------------------------------------------------------
# 2. Nim (two heaps)
# ----------------------------------------------------------------------------
def nim2_positions(M):
    """Return M+1 x M+1 table P[a][b]; True iff (a,b) is a P-position."""
    P = [[None] * (M + 1) for _ in range(M + 1)]
    P[0][0] = True
    for s in range(1, 2 * M + 1):        # process by total tokens s = a + b
        for a in range(M + 1):
            b = s - a
            if not (0 <= b <= M):
                continue
            win = any(P[a2][b] is True for a2 in range(a)) \
               or any(P[a][b2] is True for b2 in range(b))
            P[a][b] = not win
    return P


# ----------------------------------------------------------------------------
# 3. Wythoff's game (two heaps)
# ----------------------------------------------------------------------------
def wythoff_positions(M):
    """Return M+1 x M+1 table P[a][b]; True iff (a,b) is a P-position.

    Moves: reduce one heap by any amount, OR reduce BOTH heaps by the SAME
    amount.  Last token wins (normal play).
    """
    P = [[None] * (M + 1) for _ in range(M + 1)]
    P[0][0] = True
    for s in range(1, 2 * M + 1):
        for a in range(M + 1):
            b = s - a
            if not (0 <= b <= M):
                continue
            win = False
            for a2 in range(a):                      # reduce heap A
                if P[a2][b] is True:
                    win = True; break
            if not win:
                for b2 in range(b):                  # reduce heap B
                    if P[a][b2] is True:
                        win = True; break
            if not win:
                for d in range(1, min(a, b) + 1):    # reduce both equally
                    if P[a - d][b - d] is True:
                        win = True; break
            P[a][b] = not win
    return P


# ----------------------------------------------------------------------------
# Winning strategies (Task 2): from any N-position, name the winning move
# ----------------------------------------------------------------------------
PHI = (1 + np.sqrt(5)) / 2


def subtraction_strategy(n, k):
    """Winning move for subtraction game S={1..k}.  Returns the number of tokens
    to take, or None if n is a P-position (losing)."""
    r = n % (k + 1)
    return None if r == 0 else r


def nim_strategy(piles):
    """Winning move for multi-heap Nim (Bouton's nim-sum rule).
    Returns (heap_index, new_size) or None if the position is P."""
    s = 0
    for p in piles:
        s ^= p
    if s == 0:
        return None                       # P-position: nim-sum already 0
    k = s.bit_length() - 1                # highest set bit of the nim-sum
    for i, p in enumerate(piles):
        if p & (1 << k):                  # this heap shares that top bit
            return (i, p ^ s)             # p ^ s < p, a legal reduction
    return None


def wythoff_strategy(a, b):
    """Winning move for Wythoff's game.  Returns (kind, arg) or None if P.
    kind: 'both'   -> remove `arg` from BOTH heaps;
          'larger' -> set the LARGER heap to `arg` (its Wythoff partner)."""
    x, y = min(a, b), max(a, b)
    d = y - x
    t = int(np.floor(d * PHI))
    if x == t:
        return None                       # P-position (x = floor(d*phi))
    if x > t:
        return ("both", x - t)            # remove x-t from BOTH heaps
    # x < t : pair x with its Wythoff partner, then set the larger heap to it.
    #   x = floor(n*phi)   (lower a_n) -> partner is floor(n*phi^2) = b_n
    #   x = floor(n*phi^2) (upper b_n) -> partner is floor(n*phi)   = a_n
    for n in range(x + 2):
        if int(np.floor(n * PHI)) == x:
            return ("larger", int(np.floor(n * PHI * PHI)))
        if int(np.floor(n * PHI * PHI)) == x:
            return ("larger", int(np.floor(n * PHI)))
    return None


# ----------------------------------------------------------------------------
# Verification
# ----------------------------------------------------------------------------

def verify_all():
    report = []
    report.append("=" * 66)
    report.append("P023 — Task 1: winning/losing positions (brute force vs theory)")
    report.append("=" * 66)

    # --- subtraction game, k = 3 ---
    k, N = 3, 31
    Psub = subtraction_positions(k, N)
    p_list = [n for n in range(N + 1) if Psub[n]]
    theory = [n for n in range(N + 1) if n % (k + 1) == 0]
    ok = (p_list == theory)
    report.append("\n[1] Subtraction game  S = {1,2,3}  (n = 0..%d)" % N)
    report.append("    P-positions found : %s" % p_list)
    report.append("    Theory (n ≡ 0 mod %d) : %s" % (k + 1, theory))
    report.append("    MATCH: %s" % ("YES" if ok else "NO  *** MISMATCH ***"))

    # --- nim, two heaps ---
    M = 15
    Pnim = nim2_positions(M)
    mismatches = 0
    for a in range(M + 1):
        for b in range(M + 1):
            if Pnim[a][b] != ((a ^ b) == 0):
                mismatches += 1
    report.append("\n[2] Nim (two heaps, a,b = 0..%d)" % M)
    report.append("    Theory: P  <=>  a XOR b = 0  (nim-sum = 0)")
    report.append("    Cells matching theory: %d / %d" %
                  ((M + 1) ** 2 - mismatches, (M + 1) ** 2))
    report.append("    MATCH: %s" % ("YES" if mismatches == 0 else "NO  *** %d mismatches ***" % mismatches))

    # --- wythoff ---
    Mw = 24
    Pw = wythoff_positions(Mw)
    found = [(a, b) for a in range(Mw + 1) for b in range(Mw + 1)
             if Pw[a][b] and a <= b]
    found.sort(key=lambda t: (t[0] + t[1], t[0]))
    theory_w = [(int(np.floor(n * PHI)), int(np.floor(n * PHI * PHI)))
                for n in range(0, 40)]
    theory_w = [(a, b) for (a, b) in theory_w if b <= Mw and a <= Mw]
    ok_w = (found == theory_w)
    report.append("\n[3] Wythoff's game (two heaps, a,b = 0..%d)" % Mw)
    report.append("    P-positions found (a<=b): %s" % found)
    report.append("    Theory (floor(n*phi), floor(n*phi^2)): %s" % theory_w)
    report.append("    MATCH: %s" % ("YES" if ok_w else "NO  *** MISMATCH ***"))

    report.append("\n" + "=" * 66)
    report.append("phi = %.10f  (golden ratio)" % PHI)
    report.append("=" * 66)
    return "\n".join(report)


def verify_strategies():
    """Check the winning-strategy function on EVERY position in range:
    * from every N-position it must name a legal move that lands on a P-position;
    * from every P-position it must return None.
    """
    report = []
    report.append("=" * 66)
    report.append("Winning strategies (Task 2): strategy names a winning move")
    report.append("from every N-position, and none from every P-position")
    report.append("=" * 66)

    # --- subtraction game ---
    k, N = 3, 31
    Psub = subtraction_positions(k, N)
    ok = True
    for n in range(N + 1):
        mv = subtraction_strategy(n, k)
        if Psub[n]:
            if mv is not None:
                ok = False
        else:
            if mv is None or not (1 <= mv <= min(k, n)) or not Psub[n - mv]:
                ok = False
    report.append("\n[1] Subtraction game S={1,2,3}: strategy correct for n=0..%d  ->  %s"
                  % (N, "YES" if ok else "NO"))

    # --- nim (two heaps) ---
    M = 15
    Pnim = nim2_positions(M)
    ok = True
    for a in range(M + 1):
        for b in range(M + 1):
            mv = nim_strategy([a, b])
            if Pnim[a][b]:
                if mv is not None:
                    ok = False
            else:
                if mv is None:
                    ok = False
                else:
                    i, new = mv
                    nb = [a, b]
                    if new >= nb[i]:
                        ok = False
                    else:
                        nb[i] = new
                        if not Pnim[nb[0]][nb[1]]:
                            ok = False
    report.append("\n[2] Nim (two heaps): strategy correct for all 256 positions  ->  %s"
                  % ("YES" if ok else "NO"))

    # --- wythoff ---
    Mw = 24
    Pw = wythoff_positions(Mw)
    ok = True
    for a in range(Mw + 1):
        for b in range(Mw + 1):
            mv = wythoff_strategy(a, b)
            if Pw[a][b]:
                if mv is not None:
                    ok = False
            else:
                if mv is None:
                    ok = False
                    continue
                kind, arg = mv
                na, nb = a, b
                if kind == "both":
                    na, nb = a - arg, b - arg
                elif kind == "larger":
                    if a > b:
                        na = arg
                    else:
                        nb = arg
                else:  # 'smaller'
                    if a < b:
                        na = arg
                    else:
                        nb = arg
                if na < 0 or nb < 0 or not Pw[na][nb]:
                    ok = False
    report.append("\n[3] Wythoff: strategy correct for all 625 positions  ->  %s"
                  % ("YES" if ok else "NO"))

    # --- worked examples ---
    report.append("\nWorked examples of winning moves:")
    report.append("  Subtraction: n=11 -> take %d (leaves 8);  n=9 -> take %d (leaves 8)"
                  % (subtraction_strategy(11, 3), subtraction_strategy(9, 3)))
    for pos in [(3, 5), (12, 4), (9, 2)]:
        i, new = nim_strategy(list(pos))
        report.append("  Nim %s -> reduce heap %d to %d  (nim-sum becomes 0)" % (pos, i, new))
    for pos in [(1, 3), (2, 5), (5, 8), (6, 6), (0, 7)]:
        report.append("  Wythoff %s -> %s" % (pos, wythoff_strategy(*pos)))
    report.append("")
    return "\n".join(report)


# ----------------------------------------------------------------------------
# Plotting
# ----------------------------------------------------------------------------
def _legend(ax, loc="upper right", frameon=True):
    handles = [
        Patch(facecolor=N_COLOR, edgecolor="none", label="N-position (winning)"),
        Patch(facecolor=P_COLOR, edgecolor="none", label="P-position (losing)"),
    ]
    leg = ax.legend(handles=handles, loc=loc, frameon=frameon,
                    fontsize=9, borderpad=0.8, handlelength=1.2, handleheight=1.2)
    if frameon:
        leg.get_frame().set_edgecolor(REF_LINE)
        leg.get_frame().set_linewidth(0.8)


def _square_axes(ax, M):
    ax.set_xlim(-0.5, M + 0.5)
    ax.set_ylim(-0.5, M + 0.5)
    ax.set_aspect("equal")
    ax.set_xticks(range(0, M + 1))
    ax.set_yticks(range(0, M + 1))
    ax.tick_params(length=0)


def plot_subtraction(P, k, N, fname):
    fig, ax = plt.subplots(figsize=(11.5, 1.9))
    for n in range(N + 1):
        col = P_COLOR if P[n] else N_COLOR
        ax.add_patch(plt.Rectangle((n - 0.5, -0.5), 1, 1,
                                   facecolor=col, edgecolor=CELL_GAP, linewidth=1.5))
        txt = "#ffffff" if P[n] else "#0b0b0b"
        ax.text(n, 0, str(n), ha="center", va="center",
                color=txt, fontsize=7, weight="bold")
    ax.set_xlim(-0.5, N + 0.5)
    ax.set_ylim(-0.75, 0.75)
    ax.set_aspect("equal")
    ax.set_xticks(range(0, N + 1))
    ax.set_yticks([])
    ax.tick_params(length=0, labelsize=7)
    ax.set_xlabel("n = tokens remaining")
    ax.set_title("Subtraction game: P-positions are the "
                 "multiples of 4", fontsize=11, pad=12)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    _legend(ax, loc="upper right", frameon=True)
    fig.tight_layout()
    fig.savefig(fname, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_nim(P, M, fname):
    data = np.array([[1 if P[a][b] else 0 for b in range(M + 1)]
                     for a in range(M + 1)]).T   # .T -> x-axis = heap A, y-axis = heap B
    cmap = ListedColormap([N_COLOR, P_COLOR])
    edges = np.arange(M + 2) - 0.5
    fig, ax = plt.subplots(figsize=(6.3, 6.3))
    ax.pcolormesh(edges, edges, data, cmap=cmap, vmin=0, vmax=1,
                  edgecolors=CELL_GAP, linewidth=1.0)
    _square_axes(ax, M)
    ax.set_xlabel("heap A  (a)")
    ax.set_ylabel("heap B  (b)")
    ax.set_title("Nim (two heaps): P-positions are exactly the diagonal a = b",
                 fontsize=11, pad=12)
    _legend(ax, loc="lower right")
    fig.tight_layout()
    fig.savefig(fname, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_wythoff(P, M, fname):
    data = np.array([[1 if P[a][b] else 0 for b in range(M + 1)]
                     for a in range(M + 1)]).T   # .T -> x-axis = heap A, y-axis = heap B
    cmap = ListedColormap([N_COLOR, P_COLOR])
    edges = np.arange(M + 2) - 0.5
    fig, ax = plt.subplots(figsize=(6.6, 6.6))
    ax.pcolormesh(edges, edges, data, cmap=cmap, vmin=0, vmax=1,
                  edgecolors=CELL_GAP, linewidth=1.0)

    # theoretical P-position lines b = phi*a and b = a/phi
    x = np.linspace(0, M, 200)
    ax.plot(x, PHI * x, color=INK, lw=1.6, ls=(0, (6, 3)))
    ax.plot(x, x / PHI, color=INK, lw=1.6, ls=(0, (6, 3)))
    ax.text(M * 0.62, PHI * M * 0.62 + 0.7, r"$b=\varphi\,a$", color=INK, fontsize=10)
    ax.text(M * 0.62, M * 0.62 / PHI - 1.1, r"$b=a/\varphi$", color=INK, fontsize=10)

    _square_axes(ax, M)
    ax.set_xlabel("heap A  (a)")
    ax.set_ylabel("heap B  (b)")
    ax.set_title("Wythoff's game: P-positions lie on two golden-ratio lines",
                 fontsize=11, pad=12)
    _legend(ax, loc="lower right")
    fig.tight_layout()
    fig.savefig(fname, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_chomp(fname):
    ncols, nrows = 5, 4
    cx, cy = 2, 1              # chosen square (column, row from bottom-left)
    CHOCO = "#a3703f"
    EATEN = "#efe3cf"
    POISON = "#d03b3b"

    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    for c in range(ncols):
        for r in range(nrows):
            if (c, r) == (0, 0):
                fc = POISON
            elif c >= cx and r >= cy:
                fc = EATEN
            else:
                fc = CHOCO
            ax.add_patch(plt.Rectangle((c, r), 1, 1, facecolor=fc,
                                       edgecolor="white", linewidth=1.5))

    # highlight the chosen square
    ax.add_patch(plt.Rectangle((cx, cy), 1, 1, fill=False,
                               edgecolor=INK, linewidth=3.0))
    ax.text(cx + 0.5, cy + 0.5, "x", ha="center", va="center",
            fontsize=15, weight="bold", color=INK)
    # poison label
    ax.text(0.5, 0.5, "POISON", ha="center", va="center",
            fontsize=6.5, weight="bold", color="white")

    ax.set_xlim(-0.5, ncols + 0.5)
    ax.set_ylim(-0.5, nrows + 0.5)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title("Chomp: choose a square x and eat it together with everything\n"
                 "up-and-right of it (cream); the bottom-left square is poison",
                 fontsize=10.5, pad=10)

    handles = [
        Patch(facecolor=CHOCO, edgecolor="white", label="remaining chocolate"),
        Patch(facecolor=EATEN, edgecolor="white", label="eaten by this move"),
        Patch(facecolor=POISON, edgecolor="white", label="poison (lose if eaten)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
               fontsize=8.5, handlelength=1.4, handleheight=1.2,
               bbox_to_anchor=(0.5, 0.0))
    fig.subplots_adjust(bottom=0.16)
    fig.savefig(fname, dpi=200, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Fibonacci Nim (our original game)
#   One pile.  First move: take 1..n-1.  Later: take 1..2*(previous take).
#   Last coin wins.  P-positions = Fibonacci numbers; winning move = take the
#   smallest summand of the Zeckendorf representation (Whinihan 1963).
# ----------------------------------------------------------------------------
def fibonacci_numbers(N):
    """Fibonacci numbers 1, 2, 3, 5, 8, 13, ... (F1=1, F2=2) up to N."""
    a, b = 1, 2
    out = []
    while a <= N:
        out.append(a)
        a, b = b, a + b
    return out


def zeckendorf(n):
    """Zeckendorf representation of n: a list of non-adjacent Fibonacci numbers
    (1,2,3,5,8,...) summing to n, largest first.  Returns [] for n == 0."""
    fibs = fibonacci_numbers(n)
    parts = []
    i = len(fibs) - 1
    while n > 0 and i >= 0:
        if fibs[i] <= n:
            parts.append(fibs[i])
            n -= fibs[i]
            i -= 2              # skip the adjacent Fibonacci number
        else:
            i -= 1
    return parts


def fib_nim_positions(N):
    """P[(n, r)] == True iff (n coins, max take r) is a P-position in Fibonacci Nim."""
    P = {}
    for r in range(2 * N + 2):
        P[(0, r)] = True        # no coins left -> mover loses
    for n in range(1, N + 1):
        for r in range(2 * N + 2):
            win = any(P[(n - t, 2 * t)] for t in range(1, min(r, n) + 1))
            P[(n, r)] = not win
    return P


def fib_nim_strategy(n):
    """Winning opening move for Fibonacci Nim: take the smallest Zeckendorf
    summand.  Returns None if n is a Fibonacci number (a P-position)."""
    parts = zeckendorf(n)
    if len(parts) == 1:         # n is a Fibonacci number -> losing
        return None
    return parts[-1]            # smallest summand (parts is largest-first)


def verify_fib_nim():
    report = []
    report.append("=" * 66)
    report.append("Fibonacci Nim (our original game): P-positions & strategy")
    report.append("=" * 66)
    N = 60
    P = fib_nim_positions(N)
    fibs = fibonacci_numbers(N)

    init_P = [n for n in range(1, N + 1) if P[(n, n - 1)]]
    report.append("\n[1] Initial P-positions (first player loses), n=1..%d:" % N)
    report.append("    found  : %s" % init_P)
    report.append("    theory : %s  (the Fibonacci numbers)" % fibs)
    report.append("    MATCH: %s" % ("YES" if init_P == fibs else "NO"))

    bad = 0
    total = 0
    for n in range(1, N + 1):
        parts = zeckendorf(n)
        zmin = parts[-1] if parts else 0
        for r in range(2 * N + 2):
            total += 1
            if P[(n, r)] != (r < zmin):
                bad += 1
    report.append("\n[2] Full rule 'P(n,r)  iff  r < smallest Zeckendorf summand':")
    report.append("    states matching: %d / %d" % (total - bad, total))
    report.append("    MATCH: %s" % ("YES" if bad == 0 else "NO"))

    ok = True
    for n in range(1, N + 1):
        if P[(n, n - 1)]:
            continue
        wt = None
        for t in range(1, n):
            if P[(n - t, 2 * t)]:
                wt = t
                break
        if wt != fib_nim_strategy(n):
            ok = False
    report.append("\n[3] Winning move (= smallest Zeckendorf summand) verified")
    report.append("    for every non-Fibonacci n up to %d  ->  %s" % (N, "YES" if ok else "NO"))

    report.append("\nWorked examples:")
    for n in [4, 6, 7, 12, 20, 37]:
        parts = zeckendorf(n)
        if len(parts) == 1:
            report.append("  n=%d (Fibonacci) -> P-position, no winning move" % n)
        else:
            report.append("  n=%d = %s -> take %d (leaves %d)"
                          % (n, "+".join(map(str, parts)), parts[-1], n - parts[-1]))
    report.append("")
    return "\n".join(report)


def plot_fib_nim(fname):
    """P/N strip for Fibonacci Nim, n = 1..34.  P-positions = Fibonacci numbers."""
    N = 34
    fibs = set(fibonacci_numbers(N))
    fig, ax = plt.subplots(figsize=(11.5, 1.9))
    for n in range(1, N + 1):
        isP = n in fibs
        col = P_COLOR if isP else N_COLOR
        ax.add_patch(plt.Rectangle((n - 0.5, -0.5), 1, 1, facecolor=col,
                                   edgecolor=CELL_GAP, linewidth=1.5))
        txt = "#ffffff" if isP else "#0b0b0b"
        ax.text(n, 0, str(n), ha="center", va="center", color=txt,
                fontsize=6.5, weight="bold")
    ax.set_xlim(0.5, N + 0.5)
    ax.set_ylim(-0.75, 0.75)
    ax.set_aspect("equal")
    ax.set_xticks(range(1, N + 1))
    ax.set_yticks([])
    ax.tick_params(length=0, labelsize=6.5)
    ax.set_xlabel("n = coins at the start")
    ax.set_title("Fibonacci Nim: the P-positions are the Fibonacci numbers",
                 fontsize=11, pad=12)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    _legend(ax, loc="upper right", frameon=True)
    fig.tight_layout()
    fig.savefig(fname, dpi=200, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    figdir = os.path.join(root, "figs")
    os.makedirs(figdir, exist_ok=True)

    report = verify_all() + "\n" + verify_strategies() + "\n" + verify_fib_nim()
    with open(os.path.join(root, "results.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(report)

    # figures
    k, N = 3, 31
    plot_subtraction(subtraction_positions(k, N), k, N,
                     os.path.join(figdir, "fig1_subtraction.png"))

    M = 15
    plot_nim(nim2_positions(M), M, os.path.join(figdir, "fig2_nim.png"))

    Mw = 24
    plot_wythoff(wythoff_positions(Mw), Mw, os.path.join(figdir, "fig3_wythoff.png"))

    plot_chomp(os.path.join(figdir, "fig4_chomp.png"))

    plot_fib_nim(os.path.join(figdir, "fig5_fibonacci_nim.png"))

    print("\nFigures written to", figdir)
