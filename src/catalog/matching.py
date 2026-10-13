"""Non-intrusive, exact dimensional lookup for manually entered O-ring sizes.

This is only a catalogue coincidence check, not a physical identification,
confirmation of AS568 conformance, or an automatic size selection.
"""


def matching_sizes(sizes, id_in, id_tol_in, cs_in, cs_tol_in):
    """Return catalogue sizes matching all four inch dimensions.

    Spinboxes retain six decimals, so a strict 1e-9 input comparison safely
    allows binary floating-point representation without hiding a 0.000001"
    difference or ignoring a mismatched tolerance.
    """
    query = (id_in, id_tol_in, cs_in, cs_tol_in)
    return tuple(size for size in sizes if all(
        abs(actual - expected) <= 1e-9
        for actual, expected in zip(
            query,
            (size.id_in, size.id_tol_in, size.cs_in, size.cs_tol_in),
        )
    ))
