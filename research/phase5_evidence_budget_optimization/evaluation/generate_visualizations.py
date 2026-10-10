"""
Visualizations Generator for Vidhik Phase 5.2 Evidence Budget Optimization
Produces the 5 required research plots from real experimental data:
  1. Plot 1: Evidence budget vs overall fact recall
  2. Plot 2: Evidence budget vs critical fact recall
  3. Plot 3: Evidence budget vs legal outcome coverage
  4. Plot 4: Evidence tokens vs fact coverage
  5. Plot 5: Strategy comparison at equal evidence budgets (B=4 and B=8)
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
PLOTS_DIR = ROOT / "reports" / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# Load real results
res_df = pd.read_csv(RESULTS_DIR / "evidence_budget_results.csv")
oracle_df = pd.read_csv(RESULTS_DIR / "oracle_budget_analysis.csv")

# Filter fixed budgets
fixed_df = res_df[res_df["budget"] > 0].copy()

# Style configuration
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300
})

COLORS = {
    "BM25": "#1f77b4",
    "Hybrid_RRF": "#2ca02c",
    "Dense_BGE_M3": "#9467bd",
    "Hybrid_MMR_λ0.8": "#ff7f0e",
    "Sequential": "#7f7f7f",
    "Historical": "#d62728",
    "Oracle": "#8c564b"
}

MARKERS = {
    "BM25": "o",
    "Hybrid_RRF": "s",
    "Dense_BGE_M3": "^",
    "Hybrid_MMR_λ0.8": "D",
    "Sequential": "x",
    "Historical": "*",
    "Oracle": "--"
}


def plot1_budget_vs_overall_recall():
    fig, ax = plt.subplots(figsize=(8, 5))
    budgets = [2, 4, 6, 8, 10, 15]

    for strat in ["BM25", "Hybrid_RRF", "Dense_BGE_M3", "Hybrid_MMR_λ0.8", "Sequential"]:
        sub = fixed_df[fixed_df["strategy"] == strat].sort_values(by="budget")
        ax.plot(
            sub["budget"], sub["overall_recall"] * 100.0,
            marker=MARKERS[strat], label=strat, color=COLORS[strat], linewidth=2
        )

    # Plot Historical at B=4
    hist = res_df[res_df["strategy"] == "Historical"].iloc[0]
    ax.scatter([4], [hist["overall_recall"] * 100.0], color=COLORS["Historical"], s=140, zorder=5, marker="*", label="Historical head(4)")

    # Plot Oracle line
    sub_oracle = oracle_df[oracle_df["budget_per_doc"].isin(budgets)]
    ax.plot(
        sub_oracle["budget_per_doc"], sub_oracle["overall_recall"] * 100.0,
        label="Oracle Set-Cover (Upper Bound)", color=COLORS["Oracle"], linestyle="--", linewidth=1.8
    )

    ax.set_title("Plot 1: Evidence Budget vs Overall Fact Recall")
    ax.set_xlabel("Evidence Budget B (Contextual Windows per Document)")
    ax.set_ylabel("Overall Fact Recall (%)")
    ax.set_xticks(budgets)
    ax.set_ylim(10, 105)
    ax.legend(loc="lower right", frameon=True)
    plt.tight_layout()
    out_path = PLOTS_DIR / "plot1_budget_vs_overall_recall.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved {out_path}")


def plot2_budget_vs_critical_recall():
    fig, ax = plt.subplots(figsize=(8, 5))
    budgets = [2, 4, 6, 8, 10, 15]

    for strat in ["BM25", "Hybrid_RRF", "Dense_BGE_M3", "Hybrid_MMR_λ0.8", "Sequential"]:
        sub = fixed_df[fixed_df["strategy"] == strat].sort_values(by="budget")
        ax.plot(
            sub["budget"], sub["critical_recall"] * 100.0,
            marker=MARKERS[strat], label=strat, color=COLORS[strat], linewidth=2
        )

    # Plot Historical at B=4
    hist = res_df[res_df["strategy"] == "Historical"].iloc[0]
    ax.scatter([4], [hist["critical_recall"] * 100.0], color=COLORS["Historical"], s=140, zorder=5, marker="*", label="Historical head(4)")

    # Plot Oracle line
    sub_oracle = oracle_df[oracle_df["budget_per_doc"].isin(budgets)]
    ax.plot(
        sub_oracle["budget_per_doc"], sub_oracle["critical_recall"] * 100.0,
        label="Oracle Set-Cover", color=COLORS["Oracle"], linestyle="--", linewidth=1.8
    )

    ax.set_title("Plot 2: Evidence Budget vs Critical Fact Recall")
    ax.set_xlabel("Evidence Budget B (Contextual Windows per Document)")
    ax.set_ylabel("Critical Fact Recall (%)")
    ax.set_xticks(budgets)
    ax.set_ylim(10, 105)
    ax.legend(loc="lower right", frameon=True)
    plt.tight_layout()
    out_path = PLOTS_DIR / "plot2_budget_vs_critical_recall.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved {out_path}")


def plot3_budget_vs_legal_outcome_recall():
    fig, ax = plt.subplots(figsize=(8, 5))
    budgets = [2, 4, 6, 8, 10, 15]

    for strat in ["BM25", "Hybrid_RRF", "Dense_BGE_M3", "Hybrid_MMR_λ0.8", "Sequential"]:
        sub = fixed_df[fixed_df["strategy"] == strat].sort_values(by="budget")
        ax.plot(
            sub["budget"], sub["legal_outcome_recall"] * 100.0,
            marker=MARKERS[strat], label=strat, color=COLORS[strat], linewidth=2
        )

    # Historical point at B=4
    hist = res_df[res_df["strategy"] == "Historical"].iloc[0]
    ax.scatter([4], [hist["legal_outcome_recall"] * 100.0], color=COLORS["Historical"], s=160, zorder=5, marker="*", label="Historical head(4) (8.7%)")

    # Oracle line
    sub_oracle = oracle_df[oracle_df["budget_per_doc"].isin(budgets)]
    ax.plot(
        sub_oracle["budget_per_doc"], sub_oracle["legal_outcome_recall"] * 100.0,
        label="Oracle Set-Cover", color=COLORS["Oracle"], linestyle="--", linewidth=1.8
    )

    ax.set_title("Plot 3: Evidence Budget vs Legal Outcome Coverage")
    ax.set_xlabel("Evidence Budget B (Contextual Windows per Document)")
    ax.set_ylabel("Legal Outcome Recall (%)")
    ax.set_xticks(budgets)
    ax.set_ylim(0, 105)
    ax.legend(loc="lower right", frameon=True)
    plt.tight_layout()
    out_path = PLOTS_DIR / "plot3_budget_vs_legal_outcome_recall.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved {out_path}")


def plot4_tokens_vs_fact_coverage():
    fig, ax = plt.subplots(figsize=(8, 5))

    for strat in ["BM25", "Hybrid_RRF", "Dense_BGE_M3", "Hybrid_MMR_λ0.8", "Sequential"]:
        sub = fixed_df[fixed_df["strategy"] == strat].sort_values(by="estimated_llm_tokens")
        ax.plot(
            sub["estimated_llm_tokens"], sub["overall_recall"] * 100.0,
            marker=MARKERS[strat], label=strat, color=COLORS[strat], linewidth=1.8
        )

    # Whole document point
    whole = res_df[res_df["strategy"] == "Whole_Document"].iloc[0]
    ax.scatter(
        [whole["estimated_llm_tokens"]], [whole["overall_recall"] * 100.0],
        color="black", s=130, marker="o", zorder=5, label=f"Whole Document (100%, {int(whole['estimated_llm_tokens'])} tokens)"
    )

    # Historical point
    hist = res_df[res_df["strategy"] == "Historical"].iloc[0]
    ax.scatter(
        [hist["estimated_llm_tokens"]], [hist["overall_recall"] * 100.0],
        color=COLORS["Historical"], s=140, marker="*", zorder=5, label="Historical head(4)"
    )

    ax.set_title("Plot 4: Evidence Tokens vs Fact Coverage (Efficiency Frontier)")
    ax.set_xlabel("Total Evidence Context Tokens (9 Benchmark Documents)")
    ax.set_ylabel("Overall Fact Recall (%)")
    ax.set_ylim(10, 105)
    ax.legend(loc="lower right", frameon=True)
    plt.tight_layout()
    out_path = PLOTS_DIR / "plot4_tokens_vs_fact_coverage.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved {out_path}")


def plot5_strategy_comparison():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    strats = ["Historical", "Sequential", "Dense_BGE_M3", "Hybrid_RRF", "Hybrid_MMR_λ0.8", "BM25"]
    display_names = ["Historical", "Sequential", "Dense", "Hybrid RRF", "Hybrid MMR", "BM25"]

    # Budget B=4
    b4_df = res_df[res_df["budget"] == 4].set_index("strategy")
    # For historical
    hist = res_df[res_df["strategy"] == "Historical"].iloc[0]

    b4_overall = []
    b4_critical = []
    b4_outcome = []

    for s in strats:
        if s == "Historical":
            r = hist
        else:
            r = b4_df.loc[s]
        b4_overall.append(r["overall_recall"] * 100.0)
        b4_critical.append(r["critical_recall"] * 100.0)
        b4_outcome.append(r["legal_outcome_recall"] * 100.0)

    x = np.arange(len(strats))
    width = 0.25

    ax1.bar(x - width, b4_overall, width, label="Overall Recall", color="#1f77b4")
    ax1.bar(x, b4_critical, width, label="Critical Recall", color="#2ca02c")
    ax1.bar(x + width, b4_outcome, width, label="Legal Outcome Recall", color="#d62728")
    ax1.set_title("Equal Budget B = 4 Contextual Windows")
    ax1.set_xticks(x)
    ax1.set_xticklabels(display_names, rotation=30, ha="right")
    ax1.set_ylabel("Recall (%)")
    ax1.set_ylim(0, 100)
    ax1.legend(loc="upper left")

    # Budget B=8
    strats_b8 = ["Sequential", "Dense_BGE_M3", "Hybrid_RRF", "Hybrid_MMR_λ0.8", "BM25"]
    names_b8 = ["Sequential", "Dense", "Hybrid RRF", "Hybrid MMR", "BM25"]
    b8_df = res_df[res_df["budget"] == 8].set_index("strategy")

    b8_overall = [b8_df.loc[s]["overall_recall"] * 100.0 for s in strats_b8]
    b8_critical = [b8_df.loc[s]["critical_recall"] * 100.0 for s in strats_b8]
    b8_outcome = [b8_df.loc[s]["legal_outcome_recall"] * 100.0 for s in strats_b8]

    x2 = np.arange(len(strats_b8))
    ax2.bar(x2 - width, b8_overall, width, label="Overall Recall", color="#1f77b4")
    ax2.bar(x2, b8_critical, width, label="Critical Recall", color="#2ca02c")
    ax2.bar(x2 + width, b8_outcome, width, label="Legal Outcome Recall", color="#d62728")
    ax2.set_title("Equal Budget B = 8 Contextual Windows")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(names_b8, rotation=30, ha="right")
    ax2.legend(loc="upper left")

    plt.suptitle("Plot 5: Strategy Comparison at Equal Evidence Budgets (B=4 and B=8)")
    plt.tight_layout()
    out_path = PLOTS_DIR / "plot5_strategy_comparison_b4_b8.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved {out_path}")


if __name__ == "__main__":
    plot1_budget_vs_overall_recall()
    plot2_budget_vs_critical_recall()
    plot3_budget_vs_legal_outcome_recall()
    plot4_tokens_vs_fact_coverage()
    plot5_strategy_comparison()
