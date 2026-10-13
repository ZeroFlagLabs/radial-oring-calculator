"""Dimension-only AS568 quick-reference data. No GUI or design approval logic."""

from dataclasses import dataclass
import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "resources" / "data" / "as568_reference.json"


@dataclass(frozen=True)
class O_RingSize:
    dash: str
    id_in: float
    id_tol_in: float
    cs_in: float
    cs_tol_in: float

    @property
    def label(self) -> str:
        return f"AS568{self.dash}"


def load_as568(path: Path | None = None) -> tuple[O_RingSize, ...]:
    """Load exact listed dash numbers; reject malformed catalogue entries."""
    data = json.loads((path or DATA_FILE).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("units") != "in":
        raise ValueError("Unrecognised AS568 catalogue schema or units")
    sizes = []
    seen = set()
    for record in data["sizes"]:
        size = O_RingSize(**record)
        if (not size.dash.startswith("-") or size.dash in seen
                or size.id_in <= 0 or size.cs_in <= 0
                or not 0 <= size.id_tol_in < size.id_in
                or not 0 <= size.cs_tol_in < size.cs_in):
            raise ValueError(f"Invalid or duplicate AS568 size: {size.dash}")
        seen.add(size.dash)
        sizes.append(size)
    if not sizes:
        raise ValueError("AS568 catalogue contains no sizes")
    return tuple(sizes)
