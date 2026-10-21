"""Conceptual figures for the manuscript (model structure, feedback loops, yearly schedule).

Run from the repository root: ``python paper/figures/schematics.py``. Writes PNG and PDF next to
this file. The figures are drawn by hand with matplotlib patches; they contain no model output.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent
INK = "#1f2933"
MUTED = "#6b7785"
BLUE = "#2a78d6"  # money and the SOFA rule
ORANGE = "#eb6834"  # cartels and strategic behaviour
GREEN = "#1baf7a"  # research output and reputation
GREY = "#d9dee4"
FILL = {"blue": "#e3eefb", "orange": "#fde9df", "green": "#ddf3ea", "grey": "#f1f3f5"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "savefig.dpi": 300})


def box(ax, xy, w, h, text, fill="grey", edge=MUTED, size=9, weight="normal"):
    """Rounded box centred at ``xy``."""
    x, y = xy
    ax.add_patch(
        FancyBboxPatch(
            (x - w / 2, y - h / 2),
            w,
            h,
            boxstyle="round,pad=0.008,rounding_size=0.02",
            fc=FILL[fill],
            ec=edge,
            lw=1.0,
        )
    )
    ax.text(x, y, text, ha="center", va="center", fontsize=size, color=INK, weight=weight)


def arrow(ax, a, b, colour=INK, text=None, rad=0.0, lw=1.2, ls="-", tx=0.0, ty=0.0, size=8):
    """Arrow from ``a`` to ``b`` with an optional label at the midpoint (offset tx, ty)."""
    ax.add_patch(
        FancyArrowPatch(
            a,
            b,
            arrowstyle="-|>",
            mutation_scale=10,
            color=colour,
            lw=lw,
            ls=ls,
            connectionstyle=f"arc3,rad={rad}",
            shrinkA=2,
            shrinkB=2,
        )
    )
    if text:
        mx, my = (a[0] + b[0]) / 2 + tx, (a[1] + b[1]) / 2 + ty
        ax.text(mx, my, text, ha="center", va="center", fontsize=size, color=colour)


def _blank(ax, xlim=(0, 1), ylim=(0, 1)):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")


def label(ax, xy, text, colour=INK, size=8, ha="center", rot=0):
    ax.text(*xy, text, ha=ha, va="center", fontsize=size, color=colour, rotation=rot)


def fig_structure() -> None:
    """Figure 1: one researcher's money in one year (a) and the three cartel shapes (b)."""
    fig = plt.figure(figsize=(10.5, 4.2))
    ax = fig.add_axes([0.0, 0.0, 0.64, 1.0])
    _blank(ax, (-0.02, 1.33), (0, 0.92))
    label(ax, (0.0, 0.89), "(a) The money of one researcher i in one year", size=10, ha="left")
    w, h = 0.27, 0.12
    box(ax, (0.14, 0.72), w, h, "Base amount B\n(same for everyone)", "blue", BLUE, 8.5)
    box(ax, (0.14, 0.50), w, h, "Donations received\nfrom colleagues", "blue", BLUE, 8.5)
    box(ax, (0.14, 0.28), w, h, "Equal share of\nlast year's pool", "grey", MUTED, 8.5)
    box(ax, (0.48, 0.50), 0.20, 0.14, "Receipts\n$R_i(t)$", "blue", BLUE, 10, "bold")
    arrow(ax, (0.27, 0.70), (0.38, 0.54), BLUE)
    arrow(ax, (0.27, 0.50), (0.38, 0.50), BLUE)
    arrow(ax, (0.27, 0.30), (0.38, 0.46), MUTED)
    box(
        ax,
        (0.82, 0.72),
        w,
        h,
        "Kept for research\n$K_i = (1-\\alpha)\\,R_i(t)$",
        "green",
        GREEN,
        8.5,
    )
    box(
        ax,
        (0.82, 0.28),
        w,
        h,
        "Donated next year:\n$\\alpha\\,R_i(t)$, split by $w_i$",
        "blue",
        BLUE,
        8.5,
    )
    arrow(ax, (0.58, 0.55), (0.69, 0.70), GREEN)
    arrow(ax, (0.58, 0.45), (0.69, 0.30), BLUE)
    box(
        ax,
        (1.17, 0.72),
        0.27,
        h,
        "Output $y_i$; with\nfeedback, visibility $v_i$",
        "green",
        GREEN,
        8.5,
    )
    arrow(ax, (0.96, 0.72), (1.03, 0.72), GREEN)
    label(ax, (1.16, 0.28), "to the receipts of\nchosen colleagues", BLUE, 8)
    arrow(ax, (0.95, 0.28), (1.06, 0.28), BLUE)
    box(
        ax,
        (0.48, 0.08),
        0.54,
        0.10,
        "Platform: records all flows and applies safeguards;\ndiverted money goes to the pool",
        "grey",
        MUTED,
        8,
    )
    arrow(ax, (0.82, 0.21), (0.71, 0.10), MUTED, ls="--")
    arrow(ax, (0.25, 0.10), (0.14, 0.21), MUTED, ls="--")

    bx = fig.add_axes([0.655, 0.0, 0.345, 1.0])
    _blank(bx, (0, 1.0), (0, 1.12))
    label(bx, (0.0, 1.08), "(b) Cartel shapes (k = 5, all donations internal)", size=10, ha="left")
    ang = np.pi / 2 + np.arange(5) * 2 * np.pi / 5
    for name, cy in (("Clique", 0.86), ("Ring", 0.52), ("Star", 0.18)):
        cx, r = 0.36, 0.11
        pts = [(cx + r * np.cos(a), cy + r * np.sin(a)) for a in ang]
        if name == "Clique":
            for i in range(5):
                for j in range(i + 1, 5):
                    bx.plot(*zip(pts[i], pts[j]), color=ORANGE, lw=0.9)
            note = "members give equally\nto all other members"
        elif name == "Ring":
            for i in range(5):
                arrow(bx, pts[i], pts[(i + 1) % 5], ORANGE, lw=1.0)
            note = "each member gives\nall to the next one"
        else:
            hub = (cx, cy)
            pts = [(cx + r * np.cos(a), cy + r * np.sin(a)) for a in ang[:4]]
            for q in pts:
                arrow(bx, q, hub, ORANGE, rad=0.25, lw=0.9)
                arrow(bx, hub, q, ORANGE, rad=0.25, lw=0.9)
            pts = [*pts, hub]
            note = "spokes give to the hub;\nthe hub gives equally\nto the spokes"
        for q in pts:
            bx.add_patch(plt.Circle(q, 0.024, fc=FILL["orange"], ec=ORANGE, lw=1.2, zorder=3))
        label(bx, (0.0, cy), name, size=9.5, ha="left")
        label(bx, (0.56, cy), note, size=8, ha="left")
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig1_structure.{ext}", bbox_inches="tight")
    plt.close(fig)


def fig_loops() -> None:
    """Figure 2: feedback loops between funding, output, reputation and donations."""
    fig, ax = plt.subplots(figsize=(8.6, 4.9))
    _blank(ax, (-0.06, 1.62), (-0.06, 1.0))
    w, h = 0.30, 0.11
    box(ax, (0.80, 0.80), w, h, "Receipts $R$", "blue", BLUE)
    box(ax, (1.36, 0.58), w, h, "Funding kept $K$", "blue", BLUE)
    box(ax, (1.36, 0.28), w, h, "Research output $y$", "green", GREEN)
    box(ax, (0.80, 0.08), w, h, "Visibility $v$", "green", GREEN)
    box(ax, (0.24, 0.44), w, h, "Perceived quality $\\hat q$", "green", GREEN)
    box(ax, (0.24, 0.80), w, h, "Awareness:\nwho knows whom", "grey", MUTED)
    box(
        ax,
        (1.36, 0.93),
        0.36,
        0.09,
        "Cartel: share φ routed\nto fellow members",
        "orange",
        ORANGE,
        8.5,
    )

    arrow(ax, (0.96, 0.77), (1.21, 0.62), BLUE)
    label(ax, (1.13, 0.75), "+  share 1 − α", BLUE, ha="left")
    arrow(ax, (1.36, 0.52), (1.36, 0.34), GREEN)
    label(ax, (1.39, 0.43), "+  returns θ", GREEN, ha="left")
    arrow(ax, (1.21, 0.24), (0.96, 0.11), GREEN)
    label(ax, (1.13, 0.13), "+  feedback λ", GREEN, ha="left")
    arrow(ax, (0.65, 0.11), (0.33, 0.38), GREEN)
    label(ax, (0.44, 0.18), "+  reputation weight ω", GREEN, ha="right")
    arrow(ax, (0.33, 0.50), (0.68, 0.74), INK)
    label(ax, (0.53, 0.56), "+  sincere donors give\n    to the best-perceived", INK, ha="left")
    arrow(ax, (0.40, 0.80), (0.64, 0.80), MUTED, ls="--")
    label(ax, (0.52, 0.88), "+  only known\n    colleagues", MUTED, 7.5)
    ax.plot([0.65, -0.03, -0.03], [0.04, 0.04, 0.80], color=MUTED, lw=1.2, ls="--")
    arrow(ax, (-0.03, 0.80), (0.08, 0.80), MUTED, ls="--")
    label(
        ax,
        (0.30, -0.01),
        "+  visible researchers become known (τ; needs contact resampling)",
        MUTED,
        7.5,
    )
    arrow(ax, (1.18, 0.92), (0.96, 0.84), ORANGE)
    label(ax, (1.36, 0.845), "+  up to 1/(1 − αφ)", ORANGE)
    label(ax, (0.98, 0.44), "reputation\nloop", GREEN, 10)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig2_loops.{ext}", bbox_inches="tight")
    plt.close(fig)


def fig_schedule() -> None:
    """Figure 3: order of events within one simulated year."""
    steps = [
        (
            "1  Observe",
            "information allowed by the transparency regime (T0–T3), dated t − 1",
            "grey",
        ),
        (
            "2  Choose donations",
            "each researcher applies their strategy to the colleagues they know",
            "blue",
        ),
        (
            "3  Row safeguards",
            "conflict of interest (S1), per-recipient cap (S2); excess to the pool",
            "grey",
        ),
        (
            "4  Flows",
            "donations α R(t − 1) flow; mutual-flow (S3) and cycle (S4) discounts",
            "grey",
        ),
        (
            "5  Receipts and funding",
            "R(t) = B + pool share + donations;  K(t) = (1 − α) R(t)",
            "blue",
        ),
        (
            "6  Production",
            "output from K; with feedback (λ > 0), visibility follows output",
            "green",
        ),
        (
            "7  Audits and strategy change",
            "audits and peer reports (S5); defection; imitation; mutation",
            "orange",
        ),
        (
            "8  Turnover and records",
            "optional exit of seniors and entry of newcomers; outcomes recorded",
            "grey",
        ),
    ]
    edge = {"grey": MUTED, "blue": BLUE, "green": GREEN, "orange": ORANGE}
    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    _blank(ax, (-0.10, 1.62), (0, 1))
    ax.set_aspect("auto")
    y0, dy, bh = 0.94, 0.125, 0.085
    for i, (title, detail, fill) in enumerate(steps):
        y = y0 - i * dy
        box(ax, (0.26, y), 0.50, bh, title, fill, edge[fill], size=8.5, weight="bold")
        label(ax, (0.55, y), detail, size=8.5, ha="left")
        if i < len(steps) - 1:
            arrow(ax, (0.26, y - bh / 2 - 0.006), (0.26, y - dy + bh / 2 + 0.006), MUTED, lw=1.0)
    yl = y0 - 7 * dy
    ax.add_patch(
        FancyArrowPatch(
            (-0.005, yl),
            (-0.005, y0),
            arrowstyle="-|>",
            mutation_scale=10,
            color=MUTED,
            lw=1.0,
            ls="--",
            connectionstyle="bar,fraction=-0.08",
        )
    )
    label(ax, (-0.085, (y0 + yl) / 2), "next year", MUTED, 8, rot=90)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig3_schedule.{ext}", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_structure()
    fig_loops()
    fig_schedule()
