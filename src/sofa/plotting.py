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


# --- E1 ---------------------------------------------------------------------------------
BLUE_RAMP6 = ("#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b")
SEQ_BLUE = mpl.colors.LinearSegmentedColormap.from_list(
    "seq_blue", ["#f4f8fd", "#b7d3f6", "#5598e7", "#256abf", "#0d366b"]
)
DIV_RED_BLUE = mpl.colors.LinearSegmentedColormap.from_list(
    "div_red_blue", ["#8f2524", "#e34948", "#f0efec", "#3987e5", "#0d366b"]
)


def _cell_means(a2: pd.DataFrame, value: str) -> pd.DataFrame:
    return a2.groupby(["omega", "sigma_p", "alpha"])[value].mean().reset_index()


def e1_surfaces(df: pd.DataFrame, out: Path) -> list[Path]:
    """Gini and efficiency over α × σ_p, one column per ω (§7 E1, M2 checkpoint)."""
    a2 = df[df.mechanism == "A2"]
    omegas = sorted(a2.omega.unique())
    alphas = sorted(a2.alpha.unique())
    sigmas = sorted(a2.sigma_p.unique())
    g = _cell_means(a2, "gini")
    e = _cell_means(a2, "efficiency")
    gini_oracle = df[df.mechanism == "A1"].gini.mean()
    e_lo = min(-0.05, e.efficiency.min())
    norm_e = mpl.colors.TwoSlopeNorm(vmin=e_lo, vcenter=0.0, vmax=1.0)
    norm_g = mpl.colors.Normalize(0.0, max(g.gini.max(), gini_oracle))
    with mpl.rc_context({**STYLE, "axes.grid": False}):
        fig, axes = plt.subplots(
            2,
            len(omegas),
            figsize=(2.05 * len(omegas) + 1.4, 5.4),
            sharex=True,
            sharey=True,
            constrained_layout=True,
        )
        for c, om in enumerate(omegas):
            for r, (data, col, cmap, norm) in enumerate(
                ((g, "gini", SEQ_BLUE, norm_g), (e, "efficiency", DIV_RED_BLUE, norm_e))
            ):
                ax = axes[r, c]
                M = (
                    data[data.omega == om]
                    .pivot(index="sigma_p", columns="alpha", values=col)
                    .reindex(index=sigmas, columns=alphas)
                    .to_numpy()
                )
                ax.imshow(
                    M,
                    origin="lower",
                    aspect="auto",
                    cmap=cmap,
                    norm=norm,
                    extent=(-0.5, len(alphas) - 0.5, -0.5, len(sigmas) - 0.5),
                )
                if col == "efficiency":  # mark the efficiency-maximising α in each row
                    best = np.nanargmax(M, axis=1)
                    ax.plot(
                        best,
                        np.arange(len(sigmas)),
                        ls="none",
                        marker="o",
                        ms=4,
                        mfc="white",
                        mec=INK,
                        mew=0.8,
                    )
                    ax.contour(
                        np.arange(len(alphas)),
                        np.arange(len(sigmas)),
                        M,
                        levels=[0],
                        colors=INK,
                        linewidths=0.9,
                        linestyles="--",
                    )
                ax.set_xticks(
                    range(len(alphas)),
                    [f"{a:g}" if i % 2 == 0 else "" for i, a in enumerate(alphas)],
                )
                ax.set_yticks(range(len(sigmas)), [f"{s_:g}" for s_ in sigmas])
                if r == 0:
                    ax.set_title(f"ω = {om:g}", loc="left")
                if r == 1:
                    ax.set_xlabel("Pass-on fraction α")
                if c == 0:
                    ax.set_ylabel("Perception noise σ_p (log-sd)")
        for r, (cmap, norm, label) in enumerate(
            (
                (SEQ_BLUE, norm_g, "Gini(K)"),
                (DIV_RED_BLUE, norm_e, "Efficiency E\n(0 = equal split, 1 = oracle)"),
            )
        ):
            sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
            fig.colorbar(sm, ax=axes[r, :], shrink=0.9, pad=0.01).set_label(label)
        fig.suptitle(
            "Sincere SOFA: concentration (top) and allocative efficiency (bottom); "
            f"N = {int(df.attrs.get('N', 0)) or ''}, mean over {df.seed.nunique()} seeds. "
            "White dots: E-maximising α per row; dashed: E = 0.",
            x=0.01,
            ha="left",
            fontsize=9,
        )
        return _save(fig, out, "E1_surfaces")


def e1_lines(df: pd.DataFrame, out: Path, omega: float = 0.3) -> list[Path]:
    """Gini, E and ρ(K, q) against α, one line per σ_p, at ω = ``omega``; A0/A1 references."""
    a2 = df[(df.mechanism == "A2") & np.isclose(df.omega, omega)]
    a1 = df[df.mechanism == "A1"]
    sigmas = sorted(a2.sigma_p.unique())
    panels = (
        ("gini", "Gini(K)", a1.gini.mean(), 0.0),
        ("efficiency", "Efficiency E", 1.0, 0.0),
        ("spearman_Kq", "Spearman ρ(K, q)", 1.0, None),
    )
    with mpl.rc_context(STYLE):
        fig, axes = plt.subplots(1, 3, figsize=(11, 3.7))
        for ax, (col, label, ref1, ref0) in zip(axes, panels, strict=True):
            ax.axhline(ref1, color=INK, lw=1.0, ls="--")
            ax.annotate(
                "A1 oracle",
                (0.1, ref1),
                xytext=(0, 3),
                textcoords="offset points",
                fontsize=7.5,
                color=INK,
            )
            if ref0 is not None:
                ax.axhline(ref0, color=MUTED, lw=1.0, ls=":")
                ax.annotate(
                    "A0 equal split",
                    (0.1, ref0),
                    xytext=(0, 3),
                    textcoords="offset points",
                    fontsize=7.5,
                    color=MUTED,
                )
            for colour, sp in zip(BLUE_RAMP6, sigmas, strict=False):
                stats = a2[np.isclose(a2.sigma_p, sp)].groupby("alpha")[col].apply(_ci95)
                al = stats.index.to_numpy()
                m, lo, hi = (np.array([s_[i] for s_ in stats]) for i in range(3))
                ax.fill_between(al, lo, hi, color=colour, alpha=0.2, lw=0)
                ax.plot(al, m, color=colour, marker="o", ms=3.5, label=f"σ_p = {sp:g}")
            ax.set(xlabel="Pass-on fraction α", ylabel=label)
        h, lab = axes[0].get_legend_handles_labels()
        fig.legend(
            h,
            lab,
            loc="center left",
            bbox_to_anchor=(1.0, 0.5),
            fontsize=7.5,
            title="Perception\nnoise",
            title_fontsize=7.5,
        )
        fig.suptitle(
            f"Sincere SOFA against α (ω = {omega:g}); mean and 95 % interval over "
            f"{df.seed.nunique()} seeds",
            x=0.01,
            ha="left",
            fontsize=10,
        )
        fig.tight_layout()
        return _save(fig, out, "E1_lines")


def e1_equity(df: pd.DataFrame, out: Path, sigma_p: float = 0.5) -> list[Path]:
    """Career-stage share of K relative to population share, against α, by ω (§6)."""
    a2 = df[(df.mechanism == "A2") & np.isclose(df.sigma_p, sigma_p)]
    omegas = sorted(a2.omega.unique())
    with mpl.rc_context(STYLE):
        fig, axes = plt.subplots(1, 3, figsize=(11, 3.5), sharey=True)
        for ax, (col, name) in zip(
            axes,
            (
                ("early_ratio", "Early career"),
                ("mid_ratio", "Mid career"),
                ("senior_ratio", "Senior"),
            ),
            strict=True,
        ):
            ax.axhline(1.0, color=INK, lw=1.0, ls="--")
            for colour, om in zip(BLUE_RAMP6, omegas, strict=False):
                stats = a2[np.isclose(a2.omega, om)].groupby("alpha")[col].apply(_ci95)
                al = stats.index.to_numpy()
                m, lo, hi = (np.array([s_[i] for s_ in stats]) for i in range(3))
                ax.fill_between(al, lo, hi, color=colour, alpha=0.2, lw=0)
                ax.plot(al, m, color=colour, marker="o", ms=3.5, label=f"ω = {om:g}")
            ax.set(title=name, xlabel="Pass-on fraction α")
        axes[0].set_ylabel("Share of K ÷ population share")
        h, lab = axes[0].get_legend_handles_labels()
        fig.legend(
            h,
            lab,
            loc="center left",
            bbox_to_anchor=(1.0, 0.5),
            fontsize=7.5,
            title="Reputation\nweight",
            title_fontsize=7.5,
        )
        fig.suptitle(
            f"Equity by career stage (σ_p = {sigma_p:g}; 1 = proportional; no feedback, λ = 0)",
            x=0.01,
            ha="left",
            fontsize=10,
        )
        fig.tight_layout()
        return _save(fig, out, "E1_equity")


def plot_e1(results: Path) -> list[Path]:
    """All E1 figures from ``results/E1``."""
    import pyarrow.parquet as pq

    path = results / "E1" / "E1_cells.parquet"
    df = pd.read_parquet(path)
    meta = pq.read_schema(path).metadata or {}
    df.attrs["N"] = int(meta.get(b"sofa.N", b"0"))
    figs = results / "E1" / "figures"
    return e1_surfaces(df, figs) + e1_lines(df, figs) + e1_equity(df, figs)


PLOTTERS: dict[str, Callable[[Path], list[Path]]] = {"E0": plot_e0, "E1": plot_e1}
