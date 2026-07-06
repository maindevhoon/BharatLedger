"""
Illustrative cost-per-unit benchmarks used to calibrate synthetic data and to ground the
Red/Blue debate agents (ARCHITECTURE.md §2.3, §3.2).

IMPORTANT: these are ILLUSTRATIVE, ROUGH ORDER-OF-MAGNITUDE figures for a hackathon prototype,
not verified real-world benchmarks. They are chosen to be plausible (roughly consistent with
public reporting on Indian infrastructure costs) so that the demo's scoring behaves sensibly,
not to make any factual claim about true costs. This must be stated in docs/UI_UX_DESIGN.md's
About/Methodology page (Phase 8) as a known limitation.

median / p25 / p75 are in ₹ crore per outcome_unit.
"""
from __future__ import annotations

from pipeline.schema import Benchmark, Sector

# terrain multipliers applied to the "plain" base cost to get hilly/urban/coastal costs
TERRAIN_MULTIPLIER = {
    "plain": 1.0,
    "coastal": 1.25,
    "hilly": 1.9,
    "urban": 2.6,  # land acquisition + elevated/underground sections
}

# base (plain-terrain) median ₹cr per unit, and relative spread, per sector
_SECTOR_BASE = {
    Sector.ROADS:     {"unit": "km",      "median": 8.0,   "spread": 0.35},
    Sector.EDUCATION: {"unit": "schools", "median": 2.5,   "spread": 0.30},
    Sector.HEALTH:    {"unit": "beds",    "median": 0.55,  "spread": 0.30},
    Sector.WATER:     {"unit": "mld",     "median": 3.2,   "spread": 0.30},
    Sector.ENERGY:    {"unit": "mw",      "median": 6.5,   "spread": 0.30},
}


def build_benchmarks(country: str = "IN") -> list[Benchmark]:
    """One Benchmark row per (sector, terrain) combination."""
    rows: list[Benchmark] = []
    for sector, base in _SECTOR_BASE.items():
        for terrain, mult in TERRAIN_MULTIPLIER.items():
            median = round(base["median"] * mult, 3)
            spread = base["spread"]
            rows.append(
                Benchmark(
                    benchmark_id=f"{country.lower()}-{sector.value}-{terrain}",
                    country=country,
                    sector=sector,
                    outcome_unit=base["unit"],
                    terrain=terrain,
                    median_cost_per_unit_cr=median,
                    p25_cost_per_unit_cr=round(median * (1 - spread), 3),
                    p75_cost_per_unit_cr=round(median * (1 + spread), 3),
                    source_note=(
                        "Illustrative synthetic benchmark for hackathon prototype — "
                        "not a verified real-world figure."
                    ),
                )
            )
    return rows


# --------------------------------------------------------------------------------------
# States: 28 states + a few UTs, each tagged with its dominant terrain for cost-modeling.
# This is a simplification (a real state has multiple terrains) but is sufficient and
# reasonable for a synthetic demo dataset.
# --------------------------------------------------------------------------------------
INDIA_STATES: dict[str, str] = {
    "Andhra Pradesh": "coastal",
    "Arunachal Pradesh": "hilly",
    "Assam": "plain",
    "Bihar": "plain",
    "Chhattisgarh": "plain",
    "Goa": "coastal",
    "Gujarat": "coastal",
    "Haryana": "urban",
    "Himachal Pradesh": "hilly",
    "Jharkhand": "hilly",
    "Karnataka": "plain",
    "Kerala": "coastal",
    "Madhya Pradesh": "plain",
    "Maharashtra": "urban",
    "Manipur": "hilly",
    "Meghalaya": "hilly",
    "Mizoram": "hilly",
    "Nagaland": "hilly",
    "Odisha": "coastal",
    "Punjab": "plain",
    "Rajasthan": "plain",
    "Sikkim": "hilly",
    "Tamil Nadu": "coastal",
    "Telangana": "plain",
    "Tripura": "hilly",
    "Uttar Pradesh": "plain",
    "Uttarakhand": "hilly",
    "West Bengal": "plain",
    "Delhi": "urban",
    "Jammu and Kashmir": "hilly",
}
