from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import WorldConfig
from .models import WorldData
from .utils import rng_for


SEGMENTS = {
    "motor": {"frequency": 0.105, "mean_severity": 8_500.0, "sigma": 0.85,
              "premium_rate": 1_250.0, "pattern": [0.58, 0.25, 0.10, 0.04, 0.02, 0.01]},
    "property": {"frequency": 0.055, "mean_severity": 24_000.0, "sigma": 1.05,
                 "premium_rate": 1_700.0, "pattern": [0.68, 0.20, 0.07, 0.03, 0.015, 0.005]},
    "liability": {"frequency": 0.032, "mean_severity": 58_000.0, "sigma": 1.25,
                  "premium_rate": 1_950.0, "pattern": [0.12, 0.22, 0.24, 0.19, 0.14, 0.09]},
}

PERILS = {
    "motor": ["collision", "theft", "windscreen"],
    "property": ["fire", "flood", "escape_of_water"],
    "liability": ["injury", "professional_negligence", "product_liability"],
}

FX_RATES = {"GBP": 1.0, "EUR": 0.86, "USD": 0.78}


def _fit_pattern(pattern: list[float], development_years: int) -> np.ndarray:
    values = np.asarray(pattern, dtype=float)
    if development_years < len(values):
        values = np.r_[values[: development_years - 1], values[development_years - 1 :].sum()]
    elif development_years > len(values):
        values = np.r_[values, np.zeros(development_years - len(values))]
    return values / values.sum()


def generate_world(world_id: int, master_seed: int, config: WorldConfig) -> WorldData:
    seed = int(master_seed + world_id * 100_003)
    rng = rng_for(seed, "world")
    valuation_date = pd.Timestamp(config.valuation_year, 12, 31)
    years = list(range(config.valuation_year - config.accident_years + 1, config.valuation_year + 1))
    segment_names = list(SEGMENTS)

    policies: list[dict[str, object]] = []
    transactions: list[dict[str, object]] = []
    claims: list[dict[str, object]] = []
    transaction_number = 0
    claim_number = 0

    policy_segments = rng.choice(segment_names, size=config.n_policies, p=[0.50, 0.30, 0.20])
    for accident_year in years:
        for policy_index, segment in enumerate(policy_segments):
            policy_id = f"P{policy_index:06d}"
            exposure = float(rng.uniform(0.55, 1.0))
            parameters = SEGMENTS[str(segment)]
            premium = exposure * float(parameters["premium_rate"]) * float(rng.lognormal(0, 0.08))
            policies.append({
                "policy_id": policy_id,
                "accident_year": accident_year,
                "product": str(segment),
                "exposure": exposure,
                "premium_gbp": premium,
            })
            claim_count = int(rng.poisson(float(parameters["frequency"]) * exposure))
            for _ in range(claim_count):
                claim_number += 1
                claim_id = f"C{world_id:04d}-{claim_number:07d}"
                accident_day = int(rng.integers(0, 365))
                accident_date = pd.Timestamp(accident_year, 1, 1) + pd.Timedelta(days=accident_day)
                report_date = accident_date + pd.Timedelta(days=int(rng.gamma(2.0, 12.0)))
                sigma = float(parameters["sigma"])
                mean = float(parameters["mean_severity"])
                ultimate = float(rng.lognormal(np.log(mean) - 0.5 * sigma**2, sigma))
                ultimate = max(ultimate, 100.0)
                peril = str(rng.choice(PERILS[str(segment)]))
                claims.append({
                    "claim_id": claim_id, "policy_id": policy_id,
                    "accident_year": accident_year, "segment": str(segment),
                    "peril": peril, "accident_date": accident_date,
                    "report_date": report_date, "ultimate_gbp": ultimate,
                })

                pattern = _fit_pattern(list(parameters["pattern"]), config.development_years)
                proportions = rng.dirichlet(np.maximum(pattern * 80.0, 0.15))
                for development_year, proportion in enumerate(proportions):
                    payment_date = accident_date + pd.DateOffset(years=development_year) + pd.Timedelta(
                        days=int(rng.integers(15, 330))
                    )
                    if payment_date > valuation_date:
                        continue
                    transaction_number += 1
                    currency = "GBP"
                    if rng.random() < config.ambient_currency_rate:
                        currency = str(rng.choice(["EUR", "USD"]))
                    gbp_amount = ultimate * float(proportion)
                    amount_native = gbp_amount / FX_RATES[currency]
                    transactions.append({
                        "txn_ref": f"T{world_id:04d}-{transaction_number:08d}",
                        "claim_ref": claim_id,
                        "policy_ref": policy_id,
                        "loss_date": accident_date.strftime("%Y-%m-%d"),
                        "reported_date": report_date.strftime("%Y-%m-%d"),
                        "payment_date": payment_date.strftime("%Y-%m-%d"),
                        "paid_amount": round(amount_native, 2),
                        "ccy": currency,
                        "loss_peril": peril,
                        "product_hint": str(segment),
                        "claim_status": "open" if development_year < config.development_years - 1 else "closed",
                        "claim_description": f"{peril.replace('_', ' ')} loss notification",
                        "source_row_id": f"W{world_id:04d}-R{transaction_number:08d}",
                    })

    raw = pd.DataFrame(transactions)
    if not raw.empty and config.ambient_duplicate_rate > 0:
        duplicate_count = int(round(len(raw) * config.ambient_duplicate_rate))
        if duplicate_count:
            duplicates = raw.sample(duplicate_count, random_state=seed).copy()
            duplicates["source_row_id"] = duplicates["source_row_id"] + "-DUP"
            raw = pd.concat([raw, duplicates], ignore_index=True)
    raw = raw.sample(frac=1, random_state=seed).reset_index(drop=True) if len(raw) else raw
    policy_frame = pd.DataFrame(policies)
    truth_frame = pd.DataFrame(claims)
    true_ultimate = float(truth_frame["ultimate_gbp"].sum()) if len(truth_frame) else 0.0
    stale = {"GBP": 1.0, "EUR": 0.92, "USD": 0.72}
    return WorldData(
        world_id=world_id, seed=seed, valuation_date=valuation_date,
        raw_transactions=raw, policies=policy_frame, truth_claims=truth_frame,
        true_ultimate=true_ultimate, fx_rates=dict(FX_RATES), stale_fx_rates=stale,
    )
