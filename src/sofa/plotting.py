"""Figures: one function per figure (§9). PNG and PDF, colour-blind-safe palette.

Colours are categorical slots 1–3 of a validated colour-blind-safe palette (topology
identity, always paired with a distinct marker shape) and a single-hue blue ramp for
ordinal series such as cartel size k.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

TOPOLOGY_STYLE = {
    "clique": {"color": "#2a78d6", "marker": "o"},
    "ring": {"color": "#eb6834", "marker": "s"},
    "star": {"color": "#1baf7a", "marker": "^"},
}
BLUE_RAMP = ("#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b")  # light → dark
INK = "#3a3a38"
MUTED = "#8a8980"

STYLE = {
    "figure.dpi": 110,
    "savefig.dpi": 300,
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "#e6e5e0",
    "grid.linewidth": 0.6,
    "xtick.color": INK,
    "ytick.color": INK,
    "legend.frameon": False,
    "lines.linewidth": 2.0,
}


def _save(fig: plt.Figure, out: Path, stem: str) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths = [out / f"{stem}.png", out / f"{stem}.pdf"]
    for p in paths:
        fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    return paths


def _ci95(x: pd.Series) -> tuple[float, float, float]:
    """Mean and normal-approximation 95 % interval across seeds."""
    m, s, n = x.mean(), x.std(ddof=1), x.size
    h = 1.96 * s / np.sqrt(n) if n > 1 else 0.0
    return m, m - h, m + h


# --- E0 ---------------------------------------------------------------------------------
def e0_premium_vs_bound(prem: pd.DataFrame, out: Path) -> list[Path]:
    """Cartel premium Π against the analytic 1/(1 − αφ), one panel per topology (§2.3.5).

    Small multiples rather than overlaid topologies: for φ = 1 the aggregate premium is
    identical across topologies, so overlaid markers would hide one another.
    """
    g = prem.groupby(["alpha", "k", "phi", "topology"], as_index=False).premium.mean()
    g["bound"] = 1.0 / (1.0 - g.alpha * g.phi)
    ks = sorted(g.k.unique())
    lim = (0.95, g.bound.max() * 1.15)
    ticks = [1, 1.5, 2, 3, 5, 10]
    with mpl.rc_context(STYLE):
        fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.9), sharex=True, sharey=True)
        for ax, topo in zip(axes, TOPOLOGY_STYLE, strict=True):
            ax.plot(lim, lim, color=INK, lw=1.2, ls="--", zorder=1, label="Π = 1/(1 − αφ)")
            d = g[g.topology == topo]
            for colour, k in zip(BLUE_RAMP, ks, strict=False):
                dk = d[d.k == k]
                ax.scatter(
                    dk.bound,
                    dk.premium,
                    s=24,
                    color=colour,
                    edgecolor="white",
                    linewidth=0.6,
                    zorder=3,
                    label=f"k = {k}",
                )
            ax.set(
                xscale="log", yscale="log", xlim=lim, ylim=lim, xlabel="Analytic bound 1/(1 − αφ)"
            )
            ax.set_xticks(ticks, [str(t) for t in ticks])
            ax.set_yticks(ticks, [str(t) for t in ticks])
            ax.minorticks_off()
            ax.set_title(topo.capitalize(), loc="left")
        axes[0].set_ylabel("Simulated cartel premium Π (ratio)")
        axes[0].legend(loc="upper left", fontsize=7.5, title="Cartel size", title_fontsize=7.5)
        fig.suptitle(
            f"Cartel premium vs analytic bound (N = {int(prem.N.iloc[0])}; "
            "α ∈ {0.2, …, 0.9} × φ ∈ {0.25, …, 1}; mean over seeds)",
            x=0.01,
            ha="left",
            fontsize=10,
        )
        fig.tight_layout()
        return _save(fig, out, "E0_premium_vs_bound")


def e0_shortfall(prem: pd.DataFrame, short_n: pd.DataFrame, out: Path) -> list[Path]:
    """Relative shortfall 1 − Π/bound: (a) against α by k; (b) against N (§2.3.5, §10)."""
    d = prem[(prem.topology == "clique") & (prem.phi == 1.0)]
    ks = sorted(d.k.unique())
    with mpl.rc_context(STYLE):
        fig, (a, b) = plt.subplots(1, 2, figsize=(8.2, 3.6), gridspec_kw={"width_ratios": [1.5, 1]})
        for colour, k in zip(BLUE_RAMP, ks, strict=False):
            stats = d[d.k == k].groupby("alpha").shortfall.apply(_ci95)
            al = stats.index.to_numpy()
            m, lo, hi = (np.array([s[i] for s in stats]) * 100 for i in range(3))
            a.fill_between(al, lo, hi, color=colour, alpha=0.18, lw=0)
            a.plot(al, m, color=colour, marker="o", ms=4)
            a.annotate(
                f"k = {k}",
                (al[-1], m[-1]),
                xytext=(4, 0),
                textcoords="offset points",
                va="center",
                fontsize=7.5,
                color=INK,
            )
        a.set(
            xlabel="Pass-on fraction α",
            ylabel="Shortfall 1 − Π/bound (%)",
            title=f"(a) Clique, φ = 1, N = {int(d.N.iloc[0])}",
        )
        a.set_xlim(right=d.alpha.max() + 0.09)

        stats = short_n.groupby("N").shortfall.apply(_ci95)
        n = stats.index.to_numpy()
        m, lo, hi = (np.array([s[i] for s in stats]) * 100 for i in range(3))
        b.errorbar(
            n, m, yerr=[m - lo, hi - m], color=BLUE_RAMP[2], marker="o", ms=5, capsize=3, lw=2
        )
        for x, y in zip(n, m, strict=True):
            b.annotate(
                f"{y:.1f} %",
                (x, y),
                xytext=(6, 4),
                textcoords="offset points",
                fontsize=7.5,
                color=INK,
            )
        b.set(
            xscale="log",
            xlabel="Population size N (researchers)",
            ylabel="Shortfall 1 − Π/bound (%)",
            title="(b) k = 5, α = 0.8, φ = 1",
        )
        b.set_xticks(n, [str(int(x)) for x in n])
        b.minorticks_off()
        b.set_ylim(bottom=0)
        fig.text(
            0.0,
            -0.04,
            "Lines: mean over seeds; bands and bars: 95 % interval.",
            fontsize=7.5,
            color=MUTED,
        )
        fig.tight_layout()
        return _save(fig, out, "E0_shortfall")


def plot_e0(results: Path) -> list[Path]:
    """All E0 figures from ``results/E0``."""
    src = results / "E0"
    prem = pd.read_parquet(src / "E0_premium.parquet")
    short_n = pd.read_parquet(src / "E0_shortfall_vs_N.parquet")
    figs = src / "figures"
    return e0_premium_vs_bound(prem, figs) + e0_shortfall(prem, short_n, figs)


PLOTTERS: dict[str, Callable[[Path], list[Path]]] = {"E0": plot_e0}
