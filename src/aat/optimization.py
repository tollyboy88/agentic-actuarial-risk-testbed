from __future__ import annotations

import pandas as pd


def optimise_control_packages(capital: pd.DataFrame) -> pd.DataFrame:
    table = capital.copy()
    if table.empty:
        return table
    linear = table.loc[table["topology"] == "T1_LINEAR", "var_995"]
    reference = float(linear.iloc[0]) if len(linear) else float(table["var_995"].max())
    residual_cap = reference * 0.75
    table["residual_risk_cap"] = residual_cap
    table["feasible"] = table["var_995"] <= residual_cap
    table["capital_reduction_vs_reference"] = reference - table["var_995"]
    table["benefit_cost_ratio"] = table["capital_reduction_vs_reference"].clip(lower=0) / table[
        "annual_control_cost"
    ].replace(0, 1e-9)
    candidates = table.loc[table["feasible"]]
    selected_index = (
        candidates["total_cost_objective"].idxmin()
        if len(candidates) else table["total_cost_objective"].idxmin()
    )
    table["selected"] = False
    table.loc[selected_index, "selected"] = True
    return table.sort_values(["selected", "total_cost_objective"], ascending=[False, True])
