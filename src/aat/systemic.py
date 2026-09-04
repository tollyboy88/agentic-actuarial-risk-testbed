from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from .config import SimulationConfig
from .utils import rng_for


def systemic_stress(annual_losses: pd.DataFrame, config: SimulationConfig) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    simulations = config.capital.systemic_simulations
    firms = config.capital.systemic_firms
    for topology, group in annual_losses.groupby("topology"):
        marginal = np.sort(group["annual_loss"].to_numpy(dtype=float))
        for rho in config.capital.systemic_rhos:
            rng = rng_for(config.experiment.seed, topology, rho, "systemic")
            common = rng.standard_normal((simulations, 1))
            idiosyncratic = rng.standard_normal((simulations, firms))
            latent = np.sqrt(rho) * common + np.sqrt(1.0 - rho) * idiosyncratic
            uniforms = norm.cdf(latent)
            indices = np.minimum((uniforms * len(marginal)).astype(int), len(marginal) - 1)
            firm_losses = marginal[indices]
            sector = firm_losses.sum(axis=1)
            var = float(np.quantile(sector, config.capital.var_level))
            rows.append({
                "topology": topology, "rho": rho, "firms": firms, "simulations": simulations,
                "mean_sector_loss": float(sector.mean()), "var_995_sector": var,
                "es_995_sector": float(sector[sector >= var].mean()),
                "diversification_ratio": var / max(firms * float(np.quantile(marginal, config.capital.var_level)), 1e-9),
            })
    return pd.DataFrame(rows)

