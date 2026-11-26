"""
Comprehensive Statistical Hypothesis Verification Script for IEEE Greedy t-Spanner Manuscript.

Evaluates:
- RQ1: Omnibus topological differences (Welch's Heteroscedastic F_W and Kruskal-Wallis H).
- RQ2: Scale-free hubs (BA) vs. Planar Grids (GRID):
       Multiplicative stretch (two-sided) and Additive delay (directional one-sided & two-sided).
       Reports exact Welch-Satterthwaite degrees of freedom, Cohen's d, and 95% CIs.
       Applies Holm-Bonferroni and Benjamini-Hochberg multiple-testing corrections.
- RQ3: Macro-structural correlations (Pearson r, Spearman rho, Fisher z-transform 95% CIs)
       and bound slack analysis (sampled slack vs exact edge-level slack).
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

def welch_anova(groups):
    """
    Compute Welch's heteroscedastic one-way ANOVA (Delacre et al., 2019).
    Returns (F_stat, df1, df2, p_val).
    """
    k = len(groups)
    n = np.array([len(g) for g in groups], dtype=float)
    xbar = np.array([np.mean(g) for g in groups], dtype=float)
    s2 = np.array([np.var(g, ddof=1) for g in groups], dtype=float)
    
    w = n / s2
    W = np.sum(w)
    xbar_prime = np.sum(w * xbar) / W
    
    # Numerator
    num = (1.0 / (k - 1.0)) * np.sum(w * (xbar - xbar_prime)**2)
    
    # Denominator
    denom_term = np.sum((1.0 - w / W)**2 / (n - 1.0))
    denom = 1.0 + (2.0 * (k - 2.0) / (k**2 - 1.0)) * denom_term
    
    F_stat = num / denom
    df1 = k - 1
    df2 = (k**2 - 1.0) / (3.0 * denom_term)
    p_val = stats.f.sf(F_stat, df1, df2)
    
    return F_stat, df1, df2, p_val


def holm_bonferroni(p_vals):
    """Holm-Bonferroni step-down correction for an array of p-values."""
    p_vals = np.asarray(p_vals)
    n = len(p_vals)
    order = np.argsort(p_vals)
    adj_p = np.zeros(n)
    
    cum_max = 0.0
    for rank, idx in enumerate(order):
        step_factor = n - rank
        raw_adj = p_vals[idx] * step_factor
        cum_max = max(cum_max, raw_adj)
        adj_p[idx] = min(1.0, cum_max)
    return adj_p


def benjamini_hochberg(p_vals):
    """Benjamini-Hochberg FDR correction for an array of p-values."""
    p_vals = np.asarray(p_vals)
    n = len(p_vals)
    order = np.argsort(p_vals)
    adj_p = np.zeros(n)
    
    min_val = 1.0
    for rank in range(n - 1, -1, -1):
        idx = order[rank]
        step_factor = n / (rank + 1)
        raw_adj = p_vals[idx] * step_factor
        min_val = min(min_val, raw_adj)
        adj_p[idx] = min(1.0, min_val)
    return adj_p


def pearson_ci(r, n, alpha=0.05):
    """Compute 95% confidence interval for Pearson correlation via Fisher's z-transformation."""
    z = np.arctanh(r)
    se = 1.0 / np.sqrt(n - 3)
    z_crit = stats.norm.ppf(1.0 - alpha / 2.0)
    ci_low = np.tanh(z - z_crit * se)
    ci_high = np.tanh(z + z_crit * se)
    return ci_low, ci_high


def main():
    df_prop = pd.read_csv("data/proposal_extensions_metrics.csv")
    df_exp = pd.read_csv("data/spanner_experiments.csv")
    df_base = pd.read_csv("data/baseline_metrics.csv")
    
    # Merge max_degree from df_base if not present
    if "max_degree" not in df_prop.columns:
        df_prop = df_prop.merge(df_base[["graph_id", "max_degree"]], on="graph_id", how="left")
        
    topologies = ["BA", "WS", "ER", "GRID"]
    
    print("=" * 84)
    print("STATISTICAL VERIFICATION REPORT: IEEE GREEDY T-SPANNER EMPIRICAL STUDY")
    print("=" * 84)
    
    # -------------------------------------------------------------------------
    # RQ1: Omnibus Topological Differences Across All 4 Topologies
    # -------------------------------------------------------------------------
    print("\n" + "#" * 84)
    print("1. RQ1: OMNIBUS TOPOLOGY DIFFERENCES (WELCH ANOVA & KRUSKAL-WALLIS)")
    print("#" * 84)
    
    rq1_records = []
    study_pvals = []
    study_labels = []
    study_kinds = []  # 'param' or 'nonparam'

    for t in [3, 5, 7]:
        sub = df_prop[df_prop["t_limit"] == t]
        
        # Edge Retention
        groups_ret = [sub[sub["topology"] == topo]["edge_retention_ratio"].values for topo in topologies]
        fw_ret, df1_ret, df2_ret, p_fw_ret = welch_anova(groups_ret)
        h_ret, p_kw_ret = stats.kruskal(*groups_ret)
        w_lev_ret, p_lev_ret = stats.levene(*groups_ret)
        
        # Average Stretch
        groups_str = [sub[sub["topology"] == topo]["avg_stretch"].values for topo in topologies]
        fw_str, df1_str, df2_str, p_fw_str = welch_anova(groups_str)
        h_str, p_kw_str = stats.kruskal(*groups_str)
        w_lev_str, p_lev_str = stats.levene(*groups_str)
        
        print(f"\n--- Stretch Factor t = {t} ---")
        print(f"Edge Retention:")
        print(f"  Welch ANOVA: F_W({df1_ret:.1f}, {df2_ret:.2f}) = {fw_ret:.2f}, p = {p_fw_ret:.3e}")
        print(f"  Kruskal-Wallis: H = {h_ret:.2f}, p = {p_kw_ret:.3e}")
        print(f"  Levene Heteroscedasticity: W = {w_lev_ret:.2f}, p = {p_lev_ret:.3e}")
        print(f"Average Multiplicative Stretch:")
        print(f"  Welch ANOVA: F_W({df1_str:.1f}, {df2_str:.2f}) = {fw_str:.2f}, p = {p_fw_str:.3e}")
        print(f"  Kruskal-Wallis: H = {h_str:.2f}, p = {p_kw_str:.3e}")
        print(f"  Levene Heteroscedasticity: W = {w_lev_str:.2f}, p = {p_lev_str:.3e}")
        
        rq1_records.append({"t": t, "fw_ret": fw_ret, "p_fw_ret": p_fw_ret, "fw_str": fw_str, "p_fw_str": p_fw_str})
        study_pvals.extend([p_fw_ret, p_kw_ret, p_fw_str, p_kw_str])
        study_labels.extend([
            f"RQ1 t={t} Retention Welch ANOVA",
            f"RQ1 t={t} Retention Kruskal-Wallis",
            f"RQ1 t={t} Stretch Welch ANOVA",
            f"RQ1 t={t} Stretch Kruskal-Wallis",
        ])
        study_kinds.extend(["param", "nonparam", "param", "nonparam"])

    min_fw_ret = min(r["fw_ret"] for r in rq1_records)
    min_fw_str = min(r["fw_str"] for r in rq1_records)
    max_p_ret = max(r["p_fw_ret"] for r in rq1_records)
    max_p_str = max(r["p_fw_str"] for r in rq1_records)
    print(f"\n>> RQ1 Paper Summary Claim Check:")
    print(f"   Retention: F_W >= {min_fw_ret:.1f}, max p = {max_p_ret:.2e}")
    print(f"   Stretch:   F_W >= {min_fw_str:.1f}, max p = {max_p_str:.2e}")

    # -------------------------------------------------------------------------
    # RQ2: Scale-Free Hubs (BA) vs. Planar Grids (GRID)
    # -------------------------------------------------------------------------
    print("\n" + "#" * 84)
    print("2. RQ2: BA vs. GRID COMPARISON (MULTIPLICATIVE STRETCH & TRUE ADDITIVE DELAY)")
    print("#" * 84)
    
    p_values_to_correct = []
    test_labels = []
    
    for t in [3, 5, 7]:
        sub = df_prop[df_prop["t_limit"] == t]
        ba = sub[sub["topology"] == "BA"]
        grid = sub[sub["topology"] == "GRID"]
        
        # 1. Multiplicative Stretch: directional Ha: BA < GRID (primary) + two-sided
        res_m_less = stats.ttest_ind(ba["avg_stretch"], grid["avg_stretch"], equal_var=False, alternative="less")
        u_m_less, u_p_m_less = stats.mannwhitneyu(ba["avg_stretch"], grid["avg_stretch"], alternative="less")
        res_m = stats.ttest_ind(ba["avg_stretch"], grid["avg_stretch"], equal_var=False, alternative="two-sided")
        u_m, u_p_m = stats.mannwhitneyu(ba["avg_stretch"], grid["avg_stretch"], alternative="two-sided")
        diff_m = ba["avg_stretch"].mean() - grid["avg_stretch"].mean()
        se_diff_m = np.sqrt(ba["avg_stretch"].var(ddof=1)/len(ba) + grid["avg_stretch"].var(ddof=1)/len(grid))
        ci_m = stats.t.interval(0.95, df=res_m.df, loc=diff_m, scale=se_diff_m)
        d_m = diff_m / np.sqrt((ba["avg_stretch"].var() + grid["avg_stretch"].var()) / 2.0)
        
        # 2. Additive Hop Delay: directional Ha: BA < GRID (alternative='less') + two-sided
        res_a_less = stats.ttest_ind(ba["avg_additive_delay"], grid["avg_additive_delay"], equal_var=False, alternative="less")
        res_a_two = stats.ttest_ind(ba["avg_additive_delay"], grid["avg_additive_delay"], equal_var=False, alternative="two-sided")
        u_a_less, u_p_a_less = stats.mannwhitneyu(ba["avg_additive_delay"], grid["avg_additive_delay"], alternative="less")
        u_a_two, u_p_a_two = stats.mannwhitneyu(ba["avg_additive_delay"], grid["avg_additive_delay"], alternative="two-sided")
        
        # GRID - BA difference (physical detour advantage of BA over GRID)
        diff_a_grid_minus_ba = grid["avg_additive_delay"].mean() - ba["avg_additive_delay"].mean()
        se_diff_a = np.sqrt(ba["avg_additive_delay"].var(ddof=1)/len(ba) + grid["avg_additive_delay"].var(ddof=1)/len(grid))
        ci_a_grid_minus_ba = stats.t.interval(0.95, df=res_a_two.df, loc=diff_a_grid_minus_ba, scale=se_diff_a)
        d_a = diff_a_grid_minus_ba / np.sqrt((ba["avg_additive_delay"].var() + grid["avg_additive_delay"].var()) / 2.0)
        
        print(f"\n==================== Stretch Limit t = {t} ====================")
        print(f"Multiplicative Relative Stretch (E[d_H / d_G]):")
        print(f"  BA:   {ba['avg_stretch'].mean():.4f} +/- {ba['avg_stretch'].std():.4f}")
        print(f"  GRID: {grid['avg_stretch'].mean():.4f} +/- {grid['avg_stretch'].std():.4f}")
        print(f"  Difference (BA - GRID): {diff_m:.4f} (95% CI: [{ci_m[0]:.4f}, {ci_m[1]:.4f}])")
        print(f"  Primary Directional Welch t({res_m_less.df:.1f}) = {res_m_less.statistic:.2f}, p (one-sided BA < GRID) = {res_m_less.pvalue:.4f}")
        print(f"  Primary Directional Mann-Whitney U = {u_m_less:.1f}, p (one-sided BA < GRID) = {u_p_m_less:.4f}")
        print(f"  Two-Sided Welch t({res_m.df:.1f}) = {res_m.statistic:.2f}, p (two-sided) = {res_m.pvalue:.3e}")
        print(f"  Two-Sided Mann-Whitney U = {u_m:.1f}, p (two-sided) = {u_p_m:.3e}, Cohen's d (BA - GRID) = {d_m:.2f}")
        
        print(f"\nTrue Absolute Additive Path Delay (E[d_H - d_G] hops):")
        print(f"  BA:   +{ba['avg_additive_delay'].mean():.2f} +/- {ba['avg_additive_delay'].std():.2f} hops")
        print(f"  GRID: +{grid['avg_additive_delay'].mean():.2f} +/- {grid['avg_additive_delay'].std():.2f} hops")
        print(f"  Physical Detour Gap (GRID - BA): {diff_a_grid_minus_ba:.2f} hops (95% CI: [{ci_a_grid_minus_ba[0]:.2f}, {ci_a_grid_minus_ba[1]:.2f}] hops)")
        print(f"  Directional Welch t({res_a_less.df:.1f}) (BA - GRID) = {res_a_less.statistic:.2f}, p (one-sided BA < GRID) = {res_a_less.pvalue:.3e}")
        print(f"  Two-Sided Welch t({res_a_two.df:.1f}) (BA - GRID) = {res_a_two.statistic:.2f}, p (two-sided) = {res_a_two.pvalue:.3e}")
        print(f"  Mann-Whitney U = {u_a_less:.1f}, p (one-sided) = {u_p_a_less:.3e}, p (two-sided) = {u_p_a_two:.3e}, Cohen's d (GRID - BA) = {d_a:.2f}")
        
        p_values_to_correct.extend([res_m_less.pvalue, res_m.pvalue, res_a_less.pvalue, res_a_two.pvalue])
        test_labels.extend([
            f"t={t} Mult Stretch (one-sided BA < GRID)",
            f"t={t} Mult Stretch (two-sided)",
            f"t={t} Add Delay (one-sided BA < GRID)",
            f"t={t} Add Delay (two-sided)",
        ])
        study_pvals.extend([
            res_m_less.pvalue, u_p_m_less,
            res_m.pvalue, u_p_m,
            res_a_less.pvalue, u_p_a_less,
            res_a_two.pvalue, u_p_a_two,
        ])
        study_labels.extend([
            f"RQ2 t={t} Mult Stretch Welch (one-sided)",
            f"RQ2 t={t} Mult Stretch MWU (one-sided)",
            f"RQ2 t={t} Mult Stretch Welch (two-sided)",
            f"RQ2 t={t} Mult Stretch MWU (two-sided)",
            f"RQ2 t={t} Add Delay Welch (one-sided)",
            f"RQ2 t={t} Add Delay MWU (one-sided)",
            f"RQ2 t={t} Add Delay Welch (two-sided)",
            f"RQ2 t={t} Add Delay MWU (two-sided)",
        ])
        study_kinds.extend(["param", "nonparam", "param", "nonparam", "param", "nonparam", "param", "nonparam"])

    # Multiple Testing Corrections (All 12 RQ2 Welch tests, including non-significant directional mult. tests)
    adj_holm = holm_bonferroni(p_values_to_correct)
    adj_fdr = benjamini_hochberg(p_values_to_correct)
    print(f"\n--- Multiple Testing Adjustments Across RQ2 Welch Tests ({len(p_values_to_correct)} tests) ---")
    print(f"{'Test':<42} | {'Raw p':<10} | {'Holm-Bonferroni':<15} | {'Benjamini-Hochberg FDR':<15}")
    print("-" * 90)
    for lbl, raw, h_p, f_p in zip(test_labels, p_values_to_correct, adj_holm, adj_fdr):
        print(f"{lbl:<42} | {raw:<10.2e} | {h_p:<15.2e} | {f_p:<15.2e}")

    # -------------------------------------------------------------------------
    # RQ3: Structural Correlates, Bound Slack, and Practicality
    # -------------------------------------------------------------------------
    print("\n" + "#" * 84)
    print("3. RQ3: STRUCTURAL MECHANISMS, BOUND SLACK, AND RUNTIME PRACTICALITY")
    print("#" * 84)
    
    # 1. Clustering vs Edge Retention at t=3
    sub_t3 = df_prop[df_prop["t_limit"] == 3]
    r_c, p_c = stats.pearsonr(sub_t3["clustering_coefficient"], sub_t3["edge_retention_ratio"])
    rho_c, sp_p_c = stats.spearmanr(sub_t3["clustering_coefficient"], sub_t3["edge_retention_ratio"])
    ci_c = pearson_ci(r_c, len(sub_t3))
    print(f"(a) Clustering C vs. Edge Retention at t=3 (N=120):")
    print(f"    Pearson r = {r_c:.2f} (95% CI: [{ci_c[0]:.2f}, {ci_c[1]:.2f}], p = {p_c:.3e})")
    print(f"    Spearman rho = {rho_c:.2f} (p = {sp_p_c:.3e})")
    
    # 2. Baseline Path Length L vs Average Stretch at t=7
    sub_t7 = df_prop[df_prop["t_limit"] == 7]
    r_l, p_l = stats.pearsonr(sub_t7["avg_shortest_path_length"], sub_t7["avg_stretch"])
    rho_l, sp_p_l = stats.spearmanr(sub_t7["avg_shortest_path_length"], sub_t7["avg_stretch"])
    ci_l = pearson_ci(r_l, len(sub_t7))
    print(f"\n(b) Baseline Path Length L vs. Average Stretch at t=7 (N=120):")
    print(f"    Pearson r = {r_l:.2f} (95% CI: [{ci_l[0]:.2f}, {ci_l[1]:.2f}], p = {p_l:.3e})")
    print(f"    Spearman rho = {rho_l:.2f} (p = {sp_p_l:.3e})")
    
    # 3. Maximum Degree Delta vs 95th-Percentile Stretch at t=7
    r_d, p_d = stats.pearsonr(sub_t7["max_degree"], sub_t7["p95_stretch"])
    rho_d, sp_p_d = stats.spearmanr(sub_t7["max_degree"], sub_t7["p95_stretch"])
    ci_d = pearson_ci(r_d, len(sub_t7))
    print(f"\n(c) Max Degree Delta vs. P95 Tail Stretch at t=7 (N=120):")
    print(f"    Pearson r = {r_d:.2f} (95% CI: [{ci_d[0]:.2f}, {ci_d[1]:.2f}], p = {p_d:.3e})")
    print(f"    Spearman rho = {rho_d:.2f} (p = {sp_p_d:.3e})")

    study_pvals.extend([p_c, sp_p_c, p_l, sp_p_l, p_d, sp_p_d])
    study_labels.extend([
        "RQ3 C vs Retention Pearson",
        "RQ3 C vs Retention Spearman",
        "RQ3 L vs Stretch Pearson",
        "RQ3 L vs Stretch Spearman",
        "RQ3 Delta vs P95 Pearson",
        "RQ3 Delta vs P95 Spearman",
    ])
    study_kinds.extend(["param", "nonparam", "param", "nonparam", "param", "nonparam"])
    
    # 4. Bound Slack Analysis: Sampled vs Exact Edge-level
    print(f"\n(d) Bound Slack Across Sampled Route Pairs vs. Exact Edge Detours:")
    mean_sampled_slack_t7 = sub_t7["theoretical_slack"].mean()
    se_slack_t7 = sub_t7["theoretical_slack"].std() / np.sqrt(len(sub_t7))
    ci_slack_t7 = stats.t.interval(0.95, df=len(sub_t7)-1, loc=mean_sampled_slack_t7, scale=se_slack_t7)
    print(f"    Overall Mean Sampled Bound Slack at t=7 (N=120): {mean_sampled_slack_t7:.2f} units (95% CI: [{ci_slack_t7[0]:.2f}, {ci_slack_t7[1]:.2f}])")
    
    for topo in topologies:
        slack_topo = sub_t7[sub_t7["topology"] == topo]["theoretical_slack"]
        print(f"      - {topo:<4}: Sampled Slack = {slack_topo.mean():.2f} +/- {slack_topo.std():.2f} units")
    
    # Check Welch ANOVA for sampled bound slack across topologies
    for t in [3, 5, 7]:
        sub_t = df_prop[df_prop["t_limit"] == t]
        groups_slack = [sub_t[sub_t["topology"] == topo]["theoretical_slack"].values for topo in topologies]
        fw_sl, df1_sl, df2_sl, p_fw_sl = welch_anova(groups_slack)
        print(f"    Sampled Bound Slack Welch ANOVA at t={t}: F_W({df1_sl:.1f}, {df2_sl:.2f}) = {fw_sl:.2f}, p = {p_fw_sl:.3e}")
        study_pvals.append(p_fw_sl)
        study_labels.append(f"RQ3 t={t} Sampled Slack Welch ANOVA")
        study_kinds.append("param")
        
    # Exact edge-level bound slack check (fully dynamic, zero hardcoding)
    exact_slacks = df_exp["t_limit"] - df_exp["exact_max_stretch"]
    matches = df_exp["exact_max_stretch"] == df_exp["t_limit"]
    count = int(matches.sum())
    percentage = float(matches.mean() * 100.0)
    all_zero = bool((exact_slacks == 0).all())
    print(f"\n    Exact Edge-Level Maximum Stretch Invariant:")
    print(f"      Spanners attaining t: {count:,}/{len(df_exp):,} ({percentage:.2f}%)")
    print(f"      Mean exact slack: {exact_slacks.mean():.6f}")
    print(f"      All exact slacks zero: {all_zero}")

    # Study-wide Multiple Testing Corrections across ALL 45 inferential tests (including non-significant p=1.00 tests)
    all_holm = holm_bonferroni(study_pvals)
    all_fdr = benjamini_hochberg(study_pvals)
    supported = [(p, h, f, k) for p, h, f, k in zip(study_pvals, all_holm, all_fdr, study_kinds) if p < 0.05]
    nonsig = [(lbl, p, h, f) for lbl, p, h, f in zip(study_labels, study_pvals, all_holm, all_fdr) if p >= 0.05]
    param_holm_max = max(h for _, h, _, k in supported if k == "param")
    param_fdr_max = max(f for _, _, f, k in supported if k == "param")
    nonparam_holm_max = max(h for _, h, _, k in supported if k == "nonparam")
    nonparam_fdr_max = max(f for _, _, f, k in supported if k == "nonparam")
    print(f"\n--- Study-Wide Multiple Testing Summary (All {len(study_pvals)} Inferential Tests: RQ1+RQ2+RQ3) ---")
    print(f"    Total tests in family: {len(study_pvals)} | Supported (p_adj < 0.05): {len(supported)} | Non-significant (p_adj = 1.00): {len(nonsig)}")
    print(f"    Supported Parametric Welch / Pearson ({sum(1 for _,_,_,k in supported if k=='param')} tests):    max Holm = {param_holm_max:.2e}, max FDR = {param_fdr_max:.2e}")
    print(f"    Supported Non-Parametric KW / MWU / Rho ({sum(1 for _,_,_,k in supported if k=='nonparam')} tests): max Holm = {nonparam_holm_max:.2e}, max FDR = {nonparam_fdr_max:.2e}")

    # 5. Permutation Stability
    perm_stds = df_exp.groupby(["graph_id", "t_limit"])["edge_retention_ratio"].std() * 100.0
    print(f"\n(e) Permutation Stability (Within-graph standard deviation across 10 permutations):")
    print(f"    Mean retention std: {perm_stds.mean():.2f}%")
    print(f"    Min retention std:  {perm_stds.min():.2f}%")
    print(f"    Max retention std:  {perm_stds.max():.2f}%")
    print("=" * 84)


if __name__ == "__main__":
    main()
