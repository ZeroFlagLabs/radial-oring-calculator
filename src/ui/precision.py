"""Formatting for input dimensions without discarding meaningful precision."""

def format_input(value: float, minimum_decimals: int = 3) -> str:
    """Show at least 3/4 places, extending up to 6 when a value needs them.

    Inputs are stored by the spin box at six decimal places. A value such as
    0.0005 must never be presented as 0.001, even in three-decimal mode.
    """
    if minimum_decimals not in (1, 3, 4):
        raise ValueError("Input display precision must be 1, 3 or 4")
    fixed = f"{value:.6f}"
    digits = len(fixed.split(".")[1].rstrip("0"))
    return f"{value:.{max(minimum_decimals, digits)}f}"


def format_result(value: float, kind: str = 'dimension') -> str:
    """Compact, consistent presentation; caller still screens full precision.

    Input-like derived dimensions show 3 to 6 places as needed, areas 6,
    percentages 2 by default (or more for small non-zero quantities).
    """
    if kind == 'dimension':
        return format_input(value)
    if kind == 'area':
        return f'{value:.6f}'
    if kind == 'percent':
        if value != 0 and round(value, 2) == 0:
            return f'{value:.6f}'.rstrip('0').rstrip('.')
        return f'{value:.2f}'
    raise ValueError(f'Unknown result format: {kind}')
