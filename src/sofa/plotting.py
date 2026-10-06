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


# --- E2 ---------------------------------------------------------------------------------
SELECTION_STYLE = {
    "random": {"color": "#2a78d6", "marker": "o", "label": "Random"},
    "same_field": {"color": "#eb6834", "marker": "s", "label": "Same field"},
    "low_q": {"color": "#1baf7a", "marker": "^", "label": "Low quality (bottom 25 %)"},
    "high_q": {"color": "#eda100", "marker": "D", "label": "High quality (top 25 %)"},
}


def _read_with_meta(path: Path) -> pd.DataFrame:
    import pyarrow.parquet as pq

    df = pd.read_parquet(path)
    meta = pq.read_schema(path).metadata or {}
    df.attrs.update(
        {
            k.decode().removeprefix("sofa."): v.decode()
            for k, v in meta.items()
            if k.startswith(b"sofa.")
        }
    )
    return df


def e2_premium_vs_bound(df: pd.DataFrame, out: Path) -> list[Path]:
    """Π against 1/(1 − αφ) in the full model, one panel per topology (random members)."""
    d = df[df.selection == "random"].copy()
    d["N"] = int(df.attrs.get("N", 0))
    return _premium_panels(
        d, out, "E2_premium_vs_bound", "Cartel premium in the full model vs analytic bound"
    )


def _premium_panels(d: pd.DataFrame, out: Path, stem: str, title: str) -> list[Path]:
    g = d.groupby(["alpha", "k", "phi", "topology"], as_index=False).premium.mean()
    g["bound"] = 1.0 / (1.0 - g.alpha * g.phi)
    ks = sorted(g.k.unique())
    lim = (0.95, g.bound.max() * 1.15)
    ticks = [1, 1.5, 2, 3, 5, 10]
    with mpl.rc_context(STYLE):
        fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.9), sharex=True, sharey=True)
        for ax, topo in zip(axes, TOPOLOGY_STYLE, strict=True):
            ax.plot(lim, lim, color=INK, lw=1.2, ls="--", zorder=1, label="Π = 1/(1 − αφ)")
            dt = g[g.topology == topo]
            for colour, k in zip(BLUE_RAMP, ks, strict=False):
                dk = dt[dt.k == k]
                ax.scatter(
                    dk.bound,
                    dk.premium,
                    s=22,
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
        axes[0].set_ylabel("Cartel premium Π (ratio)")
        axes[0].legend(loc="upper left", fontsize=7.5, title="Cartel size", title_fontsize=7.5)
        fig.suptitle(
            f"{title} (N = {int(d.N.iloc[0])}; mean over {d.seed.nunique()} seeds)",
            x=0.01,
            ha="left",
            fontsize=10,
        )
        fig.tight_layout()
        return _save(fig, out, stem)


def e2_selection(df: pd.DataFrame, out: Path, k: int = 5, phi: float = 1.0) -> list[Path]:
    """H2: relative premium vs absolute gain by member selection (clique)."""
    d = df[(df.k == k) & (df.phi == phi) & (df.topology == "clique")].copy()
    d["gain_per_member"] = (d.premium - 1.0) * d.members_K0
    alphas = sorted(d.alpha.unique())
    with mpl.rc_context(STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
        for ax, col, label in (
            (axes[0], "premium", "Cartel premium Π (ratio)"),
            (axes[1], "gain_per_member", "Absolute gain per member (× B per year)"),
        ):
            for j, (sel, st_) in enumerate(SELECTION_STYLE.items()):
                stats = d[d.selection == sel].groupby("alpha")[col].apply(_ci95)
                al = stats.index.to_numpy() + (j - 1.5) * 0.008
                m, lo, hi = (np.array([s_[i] for s_ in stats]) for i in range(3))
                ax.errorbar(
                    al,
                    m,
                    yerr=[m - lo, hi - m],
                    color=st_["color"],
                    marker=st_["marker"],
                    ms=4.5,
                    lw=1.6,
                    capsize=2,
                    label=st_["label"],
                )
            ax.set(xlabel="Pass-on fraction α", ylabel=label)
            ax.set_xticks(alphas)
        a_line = np.linspace(min(alphas), max(alphas), 100)
        axes[0].plot(a_line, 1 / (1 - a_line * phi), color=INK, ls="--", lw=1.0)
        axes[0].annotate(
            "bound 1/(1 − αφ)",
            (0.65, 1 / (1 - 0.65 * phi)),
            xytext=(-70, 10),
            textcoords="offset points",
            fontsize=7.5,
            color=INK,
            arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.6},
        )
        axes[0].set_yscale("log")
        ticks = [1.25, 1.5, 2, 3, 5, 10]
        axes[0].set_yticks(ticks, [f"{t:g}" for t in ticks])
        axes[0].minorticks_off()
        axes[0].legend(loc="upper left", fontsize=7.5, title="Member selection", title_fontsize=7.5)
        fig.suptitle(
            f"Who forms the cartel matters for the absolute gain, not the premium "
            f"(clique, k = {k}, φ = {phi:g}; mean and 95 % interval over "
            f"{d.seed.nunique()} seeds)",
            x=0.01,
            ha="left",
            fontsize=10,
        )
        fig.tight_layout()
        return _save(fig, out, "E2_selection")


def e2_who_pays(df: pd.DataFrame, out: Path) -> list[Path]:
    """Change in K among non-members by quality decile (clique, φ = 1, random members)."""
    d = df[(df.topology == "clique") & (df.phi == 1.0) & (df.selection == "random")]
    cols = [f"who_pays_d{i}" for i in range(10)]
    ks = [k for k in (2, 5, 10, 20) if k in set(d.k)]
    with mpl.rc_context(STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
        for ax, alpha in zip(axes, (0.5, 0.8), strict=True):
            ax.axhline(0, color=INK, lw=1.0)
            for colour, k in zip(BLUE_RAMP[1:], ks, strict=False):
                dk = d[np.isclose(d.alpha, alpha) & (d.k == k)][cols]
                m = dk.mean().to_numpy() * 100
                h = 1.96 * dk.std(ddof=1).to_numpy() / np.sqrt(len(dk)) * 100
                x = np.arange(1, 11)
                ax.fill_between(x, m - h, m + h, color=colour, alpha=0.2, lw=0)
                ax.plot(x, m, color=colour, marker="o", ms=3.5, label=f"k = {k}")
            ax.set(title=f"α = {alpha:g}", xlabel="Non-members' quality decile (1 = lowest)")
            ax.set_xticks(range(1, 11))
        axes[0].set_ylabel("Mean change in K per non-member (% of B)")
        axes[0].legend(loc="lower left", fontsize=7.5, title="Cartel size", title_fontsize=7.5)
        fig.suptitle(
            "Who pays for a clique (φ = 1): change in non-members' K by their quality",
            x=0.01,
            ha="left",
            fontsize=10,
        )
        fig.tight_layout()
        return _save(fig, out, "E2_who_pays")


def plot_e2(results: Path) -> list[Path]:
    """All E2 figures."""
    df = _read_with_meta(results / "E2" / "E2_cells.parquet")
    figs = results / "E2" / "figures"
    return e2_premium_vs_bound(df, figs) + e2_selection(df, figs) + e2_who_pays(df, figs)


# --- E3 ---------------------------------------------------------------------------------
def e3_heatmaps(df: pd.DataFrame, out: Path) -> list[Path]:
    """Change against the no-strategic-agents baseline: regime × share, per behaviour."""
    metrics_ = (
        ("gini", "Δ Gini(K)"),
        ("efficiency", "Δ Efficiency E"),
        ("early_ratio", "Δ Early-career share ratio"),
    )
    behaviours = ("herder", "reciprocator", "cartel")
    names = {
        "herder": "Herders",
        "reciprocator": "Reciprocators",
        "cartel": "Cartel members (k = 5 cliques)",
    }
    regimes = sorted(df.regime.unique())
    shares = sorted(s_ for s_ in df.share.unique() if s_ > 0)
    m = df.groupby(["behaviour", "share", "regime"]).mean(numeric_only=True)
    with mpl.rc_context({**STYLE, "axes.grid": False}):
        fig, axes = plt.subplots(3, 3, figsize=(10.5, 8.2), constrained_layout=True)
        for r, (col, label) in enumerate(metrics_):
            vals = []
            for b in behaviours:
                base = m.loc[(b, 0.0)][col]
                vals.append(
                    np.array(
                        [[m.loc[(b, s_, rg)][col] - base[rg] for rg in regimes] for s_ in shares]
                    )
                )
            vmax = max(np.abs(v).max() for v in vals) or 1.0
            norm = mpl.colors.TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
            for c, (b, V) in enumerate(zip(behaviours, vals, strict=True)):
                ax = axes[r, c]
                ax.imshow(V, origin="lower", cmap=DIV_RED_BLUE, norm=norm, aspect="auto")
                for i in range(V.shape[0]):
                    for j in range(V.shape[1]):
                        ax.text(
                            j,
                            i,
                            f"{V[i, j]:+.3f}",
                            ha="center",
                            va="center",
                            fontsize=7.5,
                            color="white" if abs(V[i, j]) > 0.6 * vmax else INK,
                        )
                ax.set_xticks(range(len(regimes)), regimes)
                ax.set_yticks(range(len(shares)), [f"{s_:.0%}" for s_ in shares])
                if r == 0:
                    ax.set_title(names[b], loc="left")
                if c == 0:
                    ax.set_ylabel(f"{label}\nPopulation share")
                if r == 2:
                    ax.set_xlabel("Transparency regime")
            sm = mpl.cm.ScalarMappable(norm=norm, cmap=DIV_RED_BLUE)
            fig.colorbar(sm, ax=axes[r, :], shrink=0.85, pad=0.01).set_label(label)
        fig.suptitle(
            "Transparency × strategic behaviour: change against the all-sincere baseline "
            f"(N = {df.attrs.get('N', '?')}, mean over {df.seed.nunique()} seeds). "
            "Infeasible strategies fall back to sincere.",
            x=0.01,
            ha="left",
            fontsize=9.5,
        )
        return _save(fig, out, "E3_heatmaps")


def plot_e3(results: Path) -> list[Path]:
    """All E3 figures."""
    df = _read_with_meta(results / "E3" / "E3_cells.parquet")
    return e3_heatmaps(df, results / "E3" / "figures")


# --- E4 ---------------------------------------------------------------------------------
FAMILY_STYLE = {
    "S1": {"color": "#2a78d6", "marker": "o"},
    "S2": {"color": "#eb6834", "marker": "s"},
    "S3": {"color": "#1baf7a", "marker": "^"},
    "S4": {"color": "#eda100", "marker": "D"},
    "α": {"color": "#e87ba4", "marker": "v"},
    "Combined": {"color": "#4a3aa7", "marker": "P"},
}


def _family(name: str) -> str:
    if "+" in name:
        return "Combined"
    return "α" if name.startswith("α") else name[:2]


def e4_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per safeguard and cartel: premium, share of excess premium removed, collateral cost."""
    m = df.groupby(["safeguard", "cartel"]).mean(numeric_only=True)
    e_none = m.loc[("none", "none"), "efficiency"]
    rows = []
    for (sg, cartel), r in m.iterrows():
        if cartel == "none" or sg == "none":
            continue
        pi_none = m.loc[("none", cartel), "premium"]
        rows.append(
            dict(
                safeguard=sg,
                cartel=cartel,
                family=_family(sg),
                premium=r.premium,
                premium_none=pi_none,
                removed=(pi_none - r.premium) / (pi_none - 1.0),
                collateral=e_none - m.loc[(sg, "none"), "efficiency"],
                pool_share_sincere=m.loc[(sg, "none"), "pool_share"],
            )
        )
    return pd.DataFrame(rows)


def _place_labels(ax, x, y, labels, xspan: float, yspan: float) -> None:
    """Direct labels without collisions: merge coincident points, then nudge labels apart.

    Points closer than 1.5 % of both axis spans share one label (names joined by " = ").
    Labels sit right of their point and move up while they overlap an earlier label.
    """
    groups: list[list[int]] = []
    for i in range(len(x)):
        for g in groups:
            j = g[0]
            if abs(x[i] - x[j]) < 0.015 * xspan and abs(y[i] - y[j]) < 0.015 * yspan:
                g.append(i)
                break
        else:
            groups.append([i])
    placed: list[tuple[float, float]] = []
    dy = 0.05 * yspan
    for g in sorted(groups, key=lambda g: y[g[0]]):
        x0, y0 = x[g[0]], y[g[0]]
        ly = y0
        while any(abs(ly - py) < dy and abs(x0 - px) < 0.3 * xspan for px, py in placed):
            ly += dy
        placed.append((x0, ly))
        moved = abs(ly - y0) > 0.5 * dy
        ax.annotate(
            " = ".join(labels[i] for i in g),
            (x0, y0),
            xytext=(x0 + 0.015 * xspan, ly + (0.0 if moved else 0.01 * yspan)),
            fontsize=6.5,
            color=INK,
            va="center" if moved else "bottom",
            arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.5} if moved else None,
        )


def e4_frontier(df: pd.DataFrame, out: Path) -> list[Path]:
    """Trade-off: share of the excess premium removed vs collateral efficiency loss."""
    t = e4_table(df)
    cartels = sorted(t.cartel.unique(), key=lambda c: (c.split()[0] != "clique", c))
    with mpl.rc_context(STYLE):
        fig, axes = plt.subplots(
            1, len(cartels), figsize=(4.4 * len(cartels), 4.6), sharex=True, sharey=True
        )
        for ax, cartel in zip(np.atleast_1d(axes), cartels, strict=True):
            d = t[t.cartel == cartel]
            ax.axhline(0, color=MUTED, lw=0.8)
            ax.axvline(0, color=MUTED, lw=0.8)
            for _, r in d.iterrows():
                st_ = FAMILY_STYLE[r.family]
                ax.scatter(
                    r.collateral,
                    r.removed,
                    s=36,
                    color=st_["color"],
                    marker=st_["marker"],
                    edgecolor="white",
                    linewidth=0.6,
                    zorder=3,
                )
            _place_labels(
                ax,
                d.collateral.to_numpy(),
                d.removed.to_numpy(),
                d.safeguard.tolist(),
                xspan=t.collateral.max() - t.collateral.min(),
                yspan=t.removed.max() - t.removed.min(),
            )
            pn = d.premium_none.iloc[0]
            ax.set_title(f"{cartel.capitalize()} (Π without safeguards = {pn:.2f})", loc="left")
            ax.set_xlabel("Collateral cost: efficiency lost when all are sincere (ΔE)")
        np.atleast_1d(axes)[0].set_ylabel("Share of the cartel's excess premium removed")
        np.atleast_1d(axes)[0].set_ylim(top=max(1.15, t.removed.max() + 0.2))
        handles = [
            mpl.lines.Line2D([], [], ls="none", marker=v["marker"], color=v["color"], label=k)
            for k, v in FAMILY_STYLE.items()
        ]
        fig.legend(
            handles=handles,
            loc="center left",
            bbox_to_anchor=(1.0, 0.5),
            fontsize=7.5,
            title="Safeguard",
            title_fontsize=7.5,
        )
        fig.suptitle(
            "Safeguard trade-off: better is up and to the left "
            f"(α = 0.5 unless stated; N = {df.attrs.get('N', '?')}, "
            f"{df.seed.nunique()} seeds)",
            x=0.01,
            ha="left",
            fontsize=10,
        )
        fig.tight_layout()
        return _save(fig, out, "E4_frontier")


CARTEL_STYLE = {
    "clique k=5": {"color": "#2a78d6", "marker": "o"},
    "clique k=11": {"color": "#eda100", "marker": "D"},
    "clique k=20": {"color": "#e87ba4", "marker": "v"},
    "ring k=3": {"color": "#eb6834", "marker": "s"},
    "ring k=5": {"color": "#1baf7a", "marker": "^"},
}


def e4_dotplot(df: pd.DataFrame, out: Path) -> list[Path]:
    """One row per safeguard: premium removed by cartel type, and collateral cost."""
    t = e4_table(df)
    order = [
        "S1 COI",
        "S2 c=0.2",
        "S2 c=0.1",
        "S2 c=0.05",
        "S3 δ=0.5",
        "S3 δ=1",
        "S4 L=3 δ=1",
        "S4 L=5 δ=1",
        "S4u L=3 δ=1",
        "S4u L=5 δ=1",
        "α=0.35",
        "α=0.2",
        "S3(1)+S4(L=5)",
        "S1+S2(0.1)+S3(1)",
        "S1+S2(0.1)+S3(1)+S4(L=5)",
        "S2(0.1)+S4u(L=5)",
    ]
    order = [o for o in order if o in set(t.safeguard)][::-1]
    y = {name: i for i, name in enumerate(order)}
    with mpl.rc_context(STYLE):
        fig, (a, b) = plt.subplots(
            1, 2, figsize=(10.5, 6.6), sharey=True, gridspec_kw={"width_ratios": [1.6, 1]}
        )
        a.axvline(0, color=INK, lw=0.9)
        a.axvline(1, color=MUTED, lw=0.9, ls=":")
        for j, (cartel, st_) in enumerate(CARTEL_STYLE.items()):
            d = t[t.cartel == cartel]
            a.scatter(
                d.removed,
                [y[sg] + (j - 2) * 0.13 for sg in d.safeguard],
                s=34,
                color=st_["color"],
                marker=st_["marker"],
                edgecolor="white",
                linewidth=0.6,
                zorder=3,
                label=cartel.capitalize(),
            )
        a.set(
            xlabel="Share of the cartel's excess premium removed (1 = all)",
            xlim=(min(-0.15, t.removed.min() - 0.05), 1.05),
        )
        a.set_yticks(range(len(order)), order)
        a.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.11),
            ncol=5,
            fontsize=7.5,
            title="Cartel (φ = 1)",
            title_fontsize=7.5,
        )
        coll = t.groupby("safeguard").collateral.first()
        b.barh([y[sg] for sg in order], [coll[sg] for sg in order], height=0.55, color=BLUE_RAMP[2])
        for sg in order:
            b.annotate(
                f"{coll[sg]:+.3f}",
                (max(coll[sg], 0), y[sg]),
                xytext=(3, 0),
                textcoords="offset points",
                va="center",
                fontsize=7,
                color=INK,
            )
        b.axvline(0, color=INK, lw=0.9)
        b.set(
            xlabel="Collateral cost: ΔE when all are sincere",
            xlim=(min(-0.01, coll.min() - 0.01), coll.max() * 1.25),
        )
        for ax in (a, b):
            ax.grid(axis="y", visible=False)
        fig.suptitle(
            "Safeguards against one cartel: what they remove and what they cost "
            f"(α = 0.5 unless stated; N = {df.attrs.get('N', '?')}, "
            f"{df.seed.nunique()} seeds)",
            x=0.01,
            ha="left",
            fontsize=10,
        )
        fig.tight_layout()
        return _save(fig, out, "E4_dotplot")


def plot_e4(results: Path) -> list[Path]:
    """All E4 figures (and the summary table as CSV)."""
    df = _read_with_meta(results / "E4" / "E4_cells.parquet")
    figs = results / "E4" / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    e4_table(df).round(4).to_csv(figs / "E4_table.csv", index=False)
    return [*e4_dotplot(df, figs), *e4_frontier(df, figs), figs / "E4_table.csv"]


PLOTTERS: dict[str, Callable[[Path], list[Path]]] = {
    "E0": plot_e0,
    "E1": plot_e1,
    "E2": plot_e2,
    "E3": plot_e3,
    "E4": plot_e4,
}
