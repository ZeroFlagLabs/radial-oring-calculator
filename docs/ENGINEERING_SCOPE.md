# Engineering methods, scope and limitations

## Purpose and output

The Static & Dynamic Radial O-Ring Calculator performs **dimensional screening**, not seal qualification, certification, pressure design or life prediction. Supported cases include static and reciprocating dynamic male/piston and female/cylinder radial glands, rectangular and symmetrical double-dovetail profiles, diameter/depth entry and optional groove angles/radii.

For each metric, the engine evaluates permissible independent input tolerance endpoints and provides **minimum / nominal / maximum** outputs with input witnesses in **Inspect Results**. Tolerance extrema are not arbitrary independent stacks of displayed worst cases.

## Two calculation methods

**Detailed (default):** For positively stretched male O-rings, uses a published empirical relationship for the installed **compression cross-section** in squeeze calculations. Separately uses an approximately volume-conserved **area-equivalent cross-section** for gland fill. The compression-section approximation is not squared to obtain material area. When a permitted tolerance interval crosses the piecewise 3% ID-stretch transition, squeeze extrema include states on both sides of the transition.

**Simplified:** Uses the **free-state O-ring section** for radial squeeze and its free-state circular cross-sectional material area for gland fill. It does not reduce either for male installation stretch.

**Common to both:** All input dimensions, tolerances, gland geometry, installed fit and acceptance criteria are unchanged. Both methods use the same 2D cavity area. Female groove calculations use free-state section in both methods; results are identical. Non-positively-stretched male cases may likewise give identical results. The method is recorded on Inspector/PNG/clipboard outputs.

These are alternative assumptions for the same dimensional checks, not two separate sets of acceptance criteria. Neither method is itself a seal-performance guarantee.

## Installed fit and gland geometry

Male fit is calculated from installed gland OD relative to free O-ring ID. Female fit is **OD interference** of free O-ring OD relative to gland ID. The female calculation is not obtained by comparing rod OD with free ring ID.

Gland area is a **two-dimensional machined groove cross-section plus the actual assembled radial clearance area**, including the optional wall angles, opening radii and base radii as entered. The dovetail taper is restricted to the machined groove depth and is not extrapolated into the clearance strip. It is not the three-dimensional annular seal volume. Dimension Guides are indicative and not to scale.

## Dimensional screening criteria

| Test | PASS condition |
|---|---|
| Minimum radial squeeze | >= 0.007 in |
| Maximum squeeze (static) | <= 30% |
| Maximum squeeze (reciprocating dynamic) | <= 16% |
| Male installed ID stretch | 0-5% |
| Female installed OD interference | 0-2% |
| Gland fill | 60-85% |

Criteria are inclusive. **PASS** means the dimensional screening limits have been met. **REVIEW** means engineering evaluation is appropriate; it is not automatic seal rejection. **INVALID** means geometry/inputs are not evaluable.

## Other engineering responsibilities

Evaluate pressure and extrusion gap, backup rings, elastomer compound and fluid compatibility, temperature and differential expansion, surface finish/hardness, friction and lubrication, reciprocating duty and speed, pressure cycling, decompression, installation damage and manufacturing controls independently. Screening alone cannot approve an application.

## Validation and engineering references

The release contains extensive automated numeric, tolerance, geometry, method-reporting and GUI regression tests. They do not establish correctness for every operating condition. Technical references relevant to the Detailed method and screening criteria are identified in the application's **Settings > References** panel. Manufacturer engineering publications are cited, not redistributed.

See [v2.0.1 notes](RELEASE_NOTES_v2.0.1.md) and [original v2.0.0 method notes](RELEASE_NOTES_v2.0.0.md), [third-party notices](THIRD_PARTY_NOTICES.md) and [licensing checklist](THIRD_PARTY_RELEASE_CHECKLIST.md).
