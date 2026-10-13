"""Manufacturer-informed preliminary radial-gland dimensional screening.

This is intentionally not a material, pressure, extrusion or life assessment.
The dynamic threshold is a conservative *reciprocating* screening convention.
"""

from dataclasses import dataclass
from typing import Literal

from .rectangular import MaleRectangularResults, FemaleRectangularResults

Application = Literal["static", "dynamic"]


@dataclass(frozen=True)
class ScreeningCheck:
    name: str
    within_limits: bool
    criterion: str


@dataclass(frozen=True)
class ScreeningResults:
    application: Application
    max_squeeze_percent: float
    checks: tuple[ScreeningCheck, ...]

    @property
    def all_within_limits(self) -> bool:
        return all(check.within_limits for check in self.checks)

    @property
    def within_count(self) -> int:
        return sum(check.within_limits for check in self.checks)


def screen_rectangular(
    results: MaleRectangularResults | FemaleRectangularResults, application: Application,
    *, female: bool = False
) -> ScreeningResults:
    """Screen installed-condition ranges (do not pass free-state-only results).

    General screening defaults: min squeeze >=0.007 in, max squeeze <=30%
    static or <=16% dynamic reciprocating, 0-5% male installed ID stretch,
    0-2% female installed OD interference, 60-85% gland fill.
    These are chosen project limits from Parker/Freudenberg guidance.
    """
    if application not in ("static", "dynamic"):
        raise ValueError("Application must be 'static' or 'dynamic'.")

    sq_limit = 30.0 if application == "static" else 16.0
    checks = (
        ScreeningCheck(
            "Squeeze",
            results.squeeze_in.minimum >= 0.007
            and results.squeeze_percent.maximum <= sq_limit,
            f"Minimum ≥ 0.007 in; maximum ≤ {sq_limit:g}%",
        ),
        ScreeningCheck(
            "OD interference" if female else "ID stretch",
            results.stretch_percent.minimum >= 0.0
            and results.stretch_percent.maximum <= (2.0 if female else 5.0),
            "0–2% OD interference (female bore groove)" if female else "0–5% installed ID stretch (male piston groove)",
        ),
        ScreeningCheck(
            "Gland fill",
            results.gland_fill_percent.minimum >= 60.0
            and results.gland_fill_percent.maximum <= 85.0,
            "Minimum ≥ 60%; maximum ≤ 85%",
        ),
    )
    return ScreeningResults(application, sq_limit, checks)
