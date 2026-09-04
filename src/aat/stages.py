from __future__ import annotations

from copy import deepcopy
from typing import Callable

import numpy as np
import pandas as pd

from .config import WorldConfig
from .enums import Stage
from .ground_truth import PERILS, SEGMENTS
from .models import PipelineState, StageSnapshot
from .utils import hash_frame, stable_seed


CANONICAL_COLUMNS = {
    "txn_ref": "transaction_id",
    "claim_ref": "claim_id",
    "policy_ref": "policy_id",
    "loss_date": "accident_date",
    "reported_date": "report_date",
    "payment_date": "transaction_date",
    "paid_amount": "amount_native",
    "ccy": "currency",
    "loss_peril": "peril",
    "product_hint": "product_hint",
    "claim_status": "status",
    "claim_description": "description",
    "source_row_id": "lineage_id",
}

EXPECTED_LOSS_RATIOS = {"motor": 0.68, "property": 0.62, "liability": 0.72}


def _lineage(frame: pd.DataFrame | None) -> float:
    if frame is None or not len(frame) or "lineage_id" not in frame:
        return 0.0
    return float(frame["lineage_id"].notna().mean())


def _snapshot(
    state: PipelineState,
    stage: Stage,
    estimate: float,
    vector: dict[str, float],
    frame: pd.DataFrame | None,
    **details: object,
) -> None:
    state.snapshots.append(StageSnapshot(
        stage=stage, estimate=float(estimate), metric_vector={str(k): float(v) for k, v in vector.items()},
        row_count=0 if frame is None else int(len(frame)), data_hash=hash_frame(frame),
        lineage_completeness=_lineage(frame), hard_failure=state.hard_failure,
        details=dict(details),
    ))


def ingest(state: PipelineState, _: WorldConfig) -> None:
    raw = state.world.raw_transactions.copy(deep=True)
    frame = raw.rename(columns={key: value for key, value in CANONICAL_COLUMNS.items() if key in raw})
    required = set(CANONICAL_COLUMNS.values())
    missing = sorted(required - set(frame.columns))
    if missing:
        state.hard_failure = True
        for column in missing:
            frame[column] = np.nan
        state.events.append({"stage": Stage.INGEST, "event_type": "schema_violation", "missing": missing})
    for column in ("accident_date", "report_date", "transaction_date"):
        frame[column] = pd.to_datetime(frame[column], errors="coerce")
    frame["amount_native"] = pd.to_numeric(frame["amount_native"], errors="coerce")
    invalid = int(frame[["transaction_id", "claim_id", "transaction_date", "amount_native"]].isna().any(axis=1).sum())
    if invalid:
        state.hard_failure = True
    state.transactions = frame
    estimate = float(frame["amount_native"].fillna(0).sum())
    vector = frame.groupby("currency", dropna=False)["amount_native"].sum().fillna(0).to_dict()
    _snapshot(state, Stage.INGEST, estimate, vector, frame, invalid_rows=invalid, missing_columns=missing)


def reconcile(state: PipelineState, _: WorldConfig) -> None:
    if state.transactions is None:
        raise RuntimeError("INGEST must run before RECONCILE")
    frame = state.transactions.copy(deep=True)
    before = len(frame)
    frame = frame.drop_duplicates(subset=["transaction_id"], keep="first")
    valid_dates = (
        frame["transaction_date"].notna()
        & frame["accident_date"].notna()
        & (frame["transaction_date"] >= frame["accident_date"])
        & (frame["transaction_date"] <= state.world.valuation_date)
    )
    invalid_dates = int((~valid_dates).sum())
    frame = frame.loc[valid_dates].copy()
    rates = state.world.stale_fx_rates if state.fault_payload.get("stale_fx") else state.world.fx_rates
    frame["fx_rate_to_gbp"] = frame["currency"].map(rates)
    unknown_currency = int(frame["fx_rate_to_gbp"].isna().sum())
    if unknown_currency:
        state.hard_failure = True
        frame["fx_rate_to_gbp"] = frame["fx_rate_to_gbp"].fillna(1.0)
    frame["amount_gbp"] = frame["amount_native"].fillna(0.0) * frame["fx_rate_to_gbp"]
    state.transactions = frame
    vector = frame.groupby("currency", dropna=False)["amount_gbp"].sum().to_dict()
    _snapshot(
        state, Stage.RECONCILE, float(frame["amount_gbp"].sum()), vector, frame,
        duplicates_removed=before - len(frame) - invalid_dates, invalid_dates=invalid_dates,
        unknown_currency=unknown_currency, fx_source="stale" if state.fault_payload.get("stale_fx") else "current",
    )


def segment(state: PipelineState, _: WorldConfig) -> None:
    if state.transactions is None:
        raise RuntimeError("RECONCILE must run before SEGMENT")
    frame = state.transactions.copy(deep=True)
    peril_map = {peril: segment for segment, perils in PERILS.items() for peril in perils}
    frame["segment"] = frame["peril"].map(peril_map)
    if "product_hint" in frame:
        frame["segment"] = frame["segment"].fillna(frame["product_hint"])
    unknown = int(frame["segment"].isna().sum())
    frame["segment"] = frame["segment"].fillna("unknown")
    if state.fault_payload.get("semantic_swap"):
        mask = frame["claim_id"].astype(str).map(lambda value: stable_seed(value, "semantic") % 5 == 0)
        swaps = {"motor": "liability", "liability": "property", "property": "motor"}
        frame.loc[mask, "segment"] = frame.loc[mask, "segment"].map(swaps).fillna("unknown")
    frame["accident_year"] = frame["accident_date"].dt.year.astype("Int64")
    frame["development_year"] = (
        frame["transaction_date"].dt.year - frame["accident_date"].dt.year
    ).clip(lower=0).astype("Int64")
    state.segmented = frame
    vector = frame.groupby("segment")["amount_gbp"].sum().to_dict()
    _snapshot(state, Stage.SEGMENT, float(frame["amount_gbp"].sum()), vector, frame, unknown_segment_rows=unknown)


def _segment_pattern(segment: str, development_years: int) -> np.ndarray:
    values = np.asarray(SEGMENTS.get(segment, SEGMENTS["motor"])["pattern"], dtype=float)
    if development_years < len(values):
        values = np.r_[values[: development_years - 1], values[development_years - 1 :].sum()]
    elif development_years > len(values):
        values = np.r_[values, np.zeros(development_years - len(values))]
    return values / values.sum()


def model(state: PipelineState, config: WorldConfig) -> None:
    if state.segmented is None:
        raise RuntimeError("SEGMENT must run before MODEL")
    frame = state.segmented.copy(deep=True)
    frame = frame.loc[frame["development_year"].between(0, config.development_years - 1)].copy()
    incremental = frame.pivot_table(
        index=["segment", "accident_year"], columns="development_year",
        values="amount_gbp", aggfunc="sum", fill_value=0.0,
    )
    incremental = incremental.reindex(columns=range(config.development_years), fill_value=0.0)
    cumulative = incremental.cumsum(axis=1)
    state.triangle = cumulative.reset_index()

    premium = state.world.policies.groupby(["product", "accident_year"])["premium_gbp"].sum()
    estimates: list[dict[str, float | int | str]] = []
    factor_details: dict[str, list[float]] = {}
    for segment in sorted(frame["segment"].dropna().unique()):
        if segment == "unknown":
            continue
        segment_cumulative = cumulative.loc[segment]
        factors: list[float] = []
        for development in range(config.development_years - 1):
            eligible_years = [
                int(year) for year in segment_cumulative.index
                if state.world.valuation_date.year - int(year) >= development + 1
            ]
            denominator = float(segment_cumulative.loc[eligible_years, development].sum()) if eligible_years else 0.0
            numerator = float(segment_cumulative.loc[eligible_years, development + 1].sum()) if eligible_years else 0.0
            factor = numerator / denominator if denominator > 0 and numerator >= denominator else 1.0
            factors.append(max(factor, 1.0))
        if state.fault_payload.get("factor_scale"):
            scale = float(state.fault_payload["factor_scale"])
            factors = [1.0 + (factor - 1.0) * scale for factor in factors]
        factor_details[str(segment)] = factors
        pattern = _segment_pattern(str(segment), config.development_years)
        cumulative_pattern = np.cumsum(pattern)
        for accident_year in segment_cumulative.index:
            accident_year = int(accident_year)
            latest = min(state.world.valuation_date.year - accident_year, config.development_years - 1)
            paid = float(segment_cumulative.loc[accident_year, latest])
            tail_factor = float(np.prod(factors[latest:])) if latest < len(factors) else 1.0
            chain_ladder = paid * tail_factor
            expected = float(premium.get((segment, accident_year), 0.0)) * EXPECTED_LOSS_RATIOS.get(str(segment), 0.68)
            if state.fault_payload.get("stale_elr"):
                expected *= float(state.fault_payload["stale_elr"])
            reported = float(cumulative_pattern[min(latest, len(cumulative_pattern) - 1)])
            bornhuetter_ferguson = paid + expected * max(1.0 - reported, 0.0)
            estimates.append({
                "segment": str(segment), "accident_year": accident_year, "latest_development": latest,
                "paid_gbp": paid, "chain_ladder_ultimate": chain_ladder,
                "expected_ultimate": expected, "bf_ultimate": bornhuetter_ferguson,
                "maturity": reported,
            })
    estimate_frame = pd.DataFrame(estimates)
    if estimate_frame.empty:
        state.hard_failure = True
        estimate_frame = pd.DataFrame(columns=[
            "segment", "accident_year", "paid_gbp", "chain_ladder_ultimate",
            "expected_ultimate", "bf_ultimate", "maturity",
        ])
    state.model_estimates = estimate_frame
    estimate = float(estimate_frame["chain_ladder_ultimate"].sum()) if len(estimate_frame) else 0.0
    vector = estimate_frame.groupby("segment")["chain_ladder_ultimate"].sum().to_dict() if len(estimate_frame) else {}
    _snapshot(state, Stage.MODEL, estimate, vector, estimate_frame, development_factors=factor_details)


def select(state: PipelineState, _: WorldConfig) -> None:
    if state.model_estimates is None:
        raise RuntimeError("MODEL must run before SELECT")
    frame = state.model_estimates.copy(deep=True)
    credibility = (0.35 + 0.55 * frame["maturity"].fillna(0)).clip(0.35, 0.90)
    frame["selected_ultimate"] = (
        credibility * frame["chain_ladder_ultimate"]
        + (1.0 - credibility) * frame["bf_ultimate"]
    )
    if state.fault_payload.get("selection_bias"):
        frame["selected_ultimate"] *= float(state.fault_payload["selection_bias"])
    if state.fault_payload.get("drop_segment"):
        target = str(state.fault_payload["drop_segment"])
        frame = frame.loc[frame["segment"] != target].copy()
    state.selected_estimates = frame
    estimate = float(frame["selected_ultimate"].sum()) if len(frame) else 0.0
    vector = frame.groupby("segment")["selected_ultimate"].sum().to_dict() if len(frame) else {}
    _snapshot(state, Stage.SELECT, estimate, vector, frame, credibility_mean=float(credibility.mean()) if len(credibility) else 0.0)


def narrate(state: PipelineState, _: WorldConfig) -> None:
    if state.selected_estimates is None:
        raise RuntimeError("SELECT must run before NARRATE")
    frame = state.selected_estimates
    ultimate = float(frame["selected_ultimate"].sum()) if len(frame) else 0.0
    paid = float(frame["paid_gbp"].sum()) if len(frame) else 0.0
    reserve = ultimate - paid
    if state.fault_payload.get("prompt_injection") and not state.detected:
        state.fault_payload["narrative_override"] = 1.5
    if state.fault_payload.get("narrative_override"):
        ultimate *= float(state.fault_payload["narrative_override"])
        reserve = ultimate - paid
    segment_values = frame.groupby("segment")["selected_ultimate"].sum().to_dict() if len(frame) else {}
    state.report = {
        "valuation_date": str(state.world.valuation_date.date()),
        "ultimate_gbp": ultimate,
        "paid_gbp": paid,
        "reserve_gbp": reserve,
        "segment_ultimates": segment_values,
        "uncertainty_statement": "Scenario-conditioned estimate; process, parameter and agentic operational risk remain.",
        "lineage_hashes": [snapshot.data_hash for snapshot in state.snapshots],
    }
    _snapshot(state, Stage.NARRATE, ultimate, segment_values, frame, reserve_gbp=reserve)


STAGE_FUNCTIONS: dict[Stage, Callable[[PipelineState, WorldConfig], None]] = {
    Stage.INGEST: ingest,
    Stage.RECONCILE: reconcile,
    Stage.SEGMENT: segment,
    Stage.MODEL: model,
    Stage.SELECT: select,
    Stage.NARRATE: narrate,
}
