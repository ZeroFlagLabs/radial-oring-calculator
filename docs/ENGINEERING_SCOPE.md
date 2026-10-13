# Engineering scope and limitations

## Purpose

The **Static & Dynamic Radial O-Ring Calculator** provides dimensional screening for static and reciprocating radial O-ring seals. It is not a qualification test, certification, finite-element simulation, or substitute for application-specific engineering assessment.

For supported piston (male) and cylinder (female) configurations, it evaluates **minimum, nominal and maximum** radial squeeze, installed fit (piston ID stretch or cylinder OD interference), and gland fill. The **Inspect Results** window shows equations, substitutions and supporting explanations.

**PASS** means the evaluated dimensions meet the selected screening criteria. **REVIEW** means engineering evaluation is required; it does not automatically mean the seal will not function. **INVALID** means the inputs or geometry could not be evaluated.

## Two-dimensional gland geometry

Available gland area is a **two-dimensional (2D) representation** of the machined groove cross-section, accounting for relevant wall angles, base radii and opening radii, plus the rectangular radial-clearance area extending from the actual groove opening to the opposing component surface. It is not a calculation of complete three-dimensional annular seal volume.

The calculator applies the documented O-ring installation models and tolerance evaluations. In piston squeeze calculations, the manufacturer's published empirical section-reduction equations have a transition at **3% ID stretch**; the calculator considers both sides of that transition when the stretch interval crosses it. See **Settings → Assumptions**, **Settings → References**, and **Inspect Results** for the method and relevant references.

## Outside the dimensional screening

Users must independently assess, as relevant, pressure rating, extrusion clearance, backup rings, elastomer materials, temperature, thermal expansion, compatibility with fluids and gases, lubrication, friction, dynamic duty and speed, surface finish, hardness, pressure cycling, rapid gas decompression, installation damage and groove manufacture.

Dimension Guides explain the dimensional datums; they are **not to scale**.

## Validation and release status

The pre-release evaluation included six comparisons with historical Mathcad examples, three independent SolidWorks 2D double-dovetail area checks, and regression checks for the 3% piston-stretch transition. Differences in methodology, particularly piston installed-section calculations and female-groove fit, are explained in the application. Those comparisons support the evaluated cases, not every conceivable seal configuration.

Before the public v1.0.0 release, the final Windows GUI regression suite, packaged executable, embedded assets, links, notices and distribution rights must be checked. Until a GitHub Release appears, no downloadable production executable is claimed.

## References and licensing

The in-app References tab identifies the Parker, Freudenberg and James Walker publications used when developing the methods. These publications are not provided for download from this repository. Third-party libraries and reference data retain their own terms and rights. The application source is licensed under MIT; see [LICENSE](../LICENSE).
