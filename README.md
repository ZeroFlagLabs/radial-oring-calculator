# Static & Dynamic Radial O-Ring Calculator

**ZeroFlagLabs | Windows desktop application | v2.0.1**

A portable calculator for dimensional screening of **static and reciprocating dynamic radial O-ring seals**. It supports male/piston and female/cylinder glands, rectangular and symmetrical double-dovetail profiles, diameter/depth entry modes, and optional groove radii/angles.

## Windows download

Download [Radial-ORing-Calculator-v2.0.1-Windows-Portable.zip](https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/tag/v2.0.1). Extract its single executable and run `Static & Dynamic Radial O-Ring Calculator v2.0.1.exe`. No installer, Python environment or `_internal` folder is required.

The EXE is unsigned: SmartScreen or workplace policies may warn or block it. Only run software you trust, and do not disable Windows security protections.

## v2.0.1 maintenance improvements

- The Status heading and PASS/REVIEW indicators are centred above the Save PNG button.
- Nominal begins at the left edge of the Dimension Guide frame; numeric-column spacing and result values remain consistent.
- Suggested Save PNG filenames now begin with **Detailed** or **Simplified**, matching the method used, followed by the existing configuration details.
- No engineering equations, tolerance rules or screening limits were changed.

## Detailed and Simplified calculation methods (new in v2.0.0)

Select **Calculation method** directly in Application setup, and change it on the fly without re-entering dimensions.

- **Detailed (default):** Manufacturer-informed installed-condition calculations. For positive ID stretch in male/piston glands, radial squeeze uses an empirical installed compression cross-section. Material area for gland fill uses a **separate constant-volume section correction**.
- **Simplified:** Uses the **free-state O-ring cross-section** for radial squeeze and the free-state circular material area for gland fill, **without stretch-related section or material-area reductions**.

Both methods use **identical groove geometry, dimensional tolerance evaluation, installation-fit calculations and screening limits**. Female-cylinder results are identical in both methods. The adjacent information icon explains the alternatives.

**Inspect Results** displays the chosen method's equations and controlling tolerance cases. **Copy Snapshot** and **Save PNG** record which method was used. Selecting Simplified does not change the acceptance limits or certify a seal application.

## Features

- Static and reciprocating-dynamic radial seals, male and female glands.
- Rectangular and double-dovetail groove profiles, optional wall angles and opening/base radii.
- AS568 reference catalogue or manually entered O-ring ID and cross-section.
- Minimum, nominal and maximum radial squeeze, ID stretch/OD interference and gland fill.
- **Inspect Results** with method-specific workings, substitutions and tolerance witnesses.
- Eight approved Dimension Guides, compact PNG/clipboard reports and PASS/REVIEW/INVALID screening.
- Readable text and dropdowns with Windows dark mode, consistent UI spacing and convenient keyboard progression through input dimensions.

## Shared dimensional screening limits

| Measure | PASS criterion |
|---|---|
| Minimum radial squeeze | >= 0.007 in |
| Maximum squeeze, static | <= 30% |
| Maximum squeeze, reciprocating dynamic | <= 16% |
| Male/piston installed ID stretch | 0-5% |
| Female/cylinder installed OD interference | 0-2% |
| Gland fill | 60-85% |

Limits are inclusive. **PASS** indicates the selected dimensional criteria are satisfied, **REVIEW** requires engineering assessment rather than automatic rejection, and **INVALID** indicates unevaluable dimensions/geometry. This is not pressure, material, extrusion or seal-life qualification. See [Engineering scope](docs/ENGINEERING_SCOPE.md).

## Run from source on Windows

~~~powershell
py -3.13 -m venv venv
& '.\venv\Scripts\python.exe' -m pip install -r requirements.txt
& '.\venv\Scripts\python.exe' -m src.main
~~~

Run the tests:

~~~powershell
& '.\venv\Scripts\python.exe' -m unittest discover -s tests -q
~~~

## Rebuild the single portable EXE

~~~powershell
& '.\venv\Scripts\python.exe' -m pip install -r requirements-build.txt
& '.\venv\Scripts\python.exe' .\tools\Build-OneFile-Portable.py --project (Get-Location).Path
~~~

The v2 package retains the v1.0.1 one-file builder: it embeds all eight guides, UI forms, icons and AS568 data, removes two unnecessary Qt Virtual Keyboard binaries, checks the EXE inventory, and creates an EXE-only ZIP plus SHA-256 checksum.

See [Windows packaging](docs/WINDOWS_PACKAGING.md), [Qt rebuild and LGPL obligations](docs/ONEFILE_REBUILD_AND_LGPL.md), and [development instructions](docs/DEVELOPMENT.md).

## Documentation

- [v2.0.1 release notes](docs/RELEASE_NOTES_v2.0.1.md)
- [v2.0.0 feature release notes](docs/RELEASE_NOTES_v2.0.0.md)
- [Engineering methods, scope and limitations](docs/ENGINEERING_SCOPE.md)
- [Windows build and packaging](docs/WINDOWS_PACKAGING.md)
- [Third-party notices](docs/THIRD_PARTY_NOTICES.md), [release checklist](docs/THIRD_PARTY_RELEASE_CHECKLIST.md) and [licence texts](licenses/)

## Licensing and privacy

Original project code and project-created artwork are provided under [MIT](LICENSE), except independently licensed components. Qt/PySide6, Python and bundled dependencies retain their own licences and attribution/source obligations. The AS568 data is reference information and does not grant reproduction rights for manufacturer publications or underlying standards. No proprietary engineering publications, private drawings or local verification material are distributed.
