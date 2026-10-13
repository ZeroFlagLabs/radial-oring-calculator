# Engineering scope and limitations

## Purpose

The **Static & Dynamic Radial O-Ring Calculator** provides dimensional screening for static and reciprocating radial O-ring seals. It is not a qualification test, certification, finite-element simulation, or substitute for application-specific engineering assessment.

For supported piston (male) and cylinder (female) configurations, it evaluates **minimum, nominal and maximum** radial squeeze, installed fit (piston ID stretch or cylinder OD interference), and gland fill. The **Inspect Results** window shows equations, substitutions and supporting explanations.

**PASS** means the evaluated dimensions meet the selected screening criteria. **REVIEW** requires engineering evaluation; it does not automatically mean the seal cannot function. **INVALID** means the inputs or geometry could not be evaluated.

## Two-dimensional gland geometry

Available gland area is a **two-dimensional (2D) representation** of the machined groove cross-section, accounting for relevant wall angles, base radii and opening radii, plus the rectangular radial-clearance area extending from the actual groove opening to the opposing component surface. It is not the full three-dimensional annular seal volume.

For piston squeeze, the manufacturer's published section-reduction equations transition at **3% ID stretch**. The calculator evaluates both sides where the permitted stretch range crosses that transition. See **Settings → Assumptions**, **Settings → References** and **Inspect Results** for the documented method.

## Outside the dimensional screening

Evaluate independently as applicable: pressure and extrusion clearance, backup rings, elastomer materials and compatibility, temperature and thermal expansion, surface finish and hardness, lubrication and friction, dynamic duty/speed, pressure cycling, rapid gas decompression, installation damage and manufacturing constraints.

The eight Dimension Guides identify relevant datums; **they are not to scale**.

## Validation evidence and limitations

Pre-release evaluation included comparisons against **six historic Mathcad examples**, **three independent SolidWorks 2D double-dovetail area checks**, and the **3% stretch transition** regression cases. Differences in methodology, notably installed-section handling and female-groove interference, are explained within the application. The evaluated examples do not prove every possible seal configuration.

Before publishing v1.0.0, complete the Windows GUI regression suite, portable EXE and embedded-resource smoke tests, links and updater checks, and third-party source/data redistribution review.

## References and licensing

The in-app References tab cites Parker, Freudenberg and James Walker engineering publications. Publisher PDFs and private engineering documents are **not** included in the application or public repository. The application's original source is MIT licensed; third-party libraries and data have separate terms. See [LICENSE](../LICENSE) and [third-party release checklist](THIRD_PARTY_RELEASE_CHECKLIST.md).
