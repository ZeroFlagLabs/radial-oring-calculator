# Static & Dynamic Radial O-Ring Calculator

A Windows desktop application for **dimensional screening of static and reciprocating dynamic radial O-ring seals**, developed by **ZeroFlagLabs**.

The calculator supports **piston (male)** and **cylinder (female)** glands with **rectangular** and **symmetrical double-dovetail** groove profiles. It calculates minimum, nominal and maximum results across dimensional tolerances and provides detailed working in **Inspect Results**, plus a compact **PNG summary report**.

> **Pre-release status:** The application has reached v0.9.9 validation candidate. The public **v1.0.0 portable Windows release is not published yet**. The final executable, source tree and example screenshots will be added after packaging and release checks.

## Features

- Static and reciprocating dynamic radial O-ring screening.
- Piston/male and cylinder/female configurations.
- Rectangular and symmetrical double-dovetail grooves, with depth or diameter entry modes.
- Manual O-ring dimensions and an AS568 size catalogue.
- Minimum, nominal and maximum **radial squeeze**, **installed fit** (ID stretch or OD interference) and **gland fill**.
- **Two-dimensional (2D)** groove-area calculations, including wall angles, base radii and opening radii.
- Detailed **Inspect Results** showing equations, numerical substitutions and explanations.
- Dimension Guides for the supported groove/entry combinations.
- **Copy Snapshot** and **Save PNG** for a concise results report.
- **PASS** and **REVIEW** screening outcomes, plus invalid-input indication.
- Optional checking for newer stable releases on GitHub, without automatically installing them.

## Screenshots and example report

A populated screenshot of the main window and an example PNG calculation report will be included before v1.0.0.

**The application itself intentionally starts with zero-valued numeric inputs.** No example design is loaded on startup.

## Download

When v1.0.0 is published, download the portable Windows executable from [GitHub Releases](https://github.com/ZeroFlagLabs/radial-oring-calculator/releases).

The intended portable package runs without a separate Python installation. There is **no release download available yet**; the final Windows build and smoke tests are still pending.

## Running from source

These instructions apply **after the source tree has been uploaded** to this repository. The project uses Python and **PySide6**.

On Windows, using PowerShell from the project folder:

```powershell
python -m venv venv
& '.\venv\Scripts\python.exe' -m pip install -r requirements.txt
& '.\venv\Scripts\python.exe' -m src.main
```

To run the regression suite:

```powershell
& '.\venv\Scripts\python.exe' -m unittest discover -s tests -v
```

The source tree also includes `requirements-build.txt` and `tools/package_app.sh` for creating a packaged Windows executable from Git Bash.

## Engineering scope

This program performs **dimensional screening**, not full seal design approval or certification.

- **PASS** means the evaluated dimensions meet the selected screening criteria.
- **REVIEW** identifies a condition requiring further engineering assessment; it does not automatically mean the seal design is unsuitable.
- **INVALID** means dimensions or geometry could not be evaluated.

The available gland area is a **two-dimensional (2D) representation** of the machined groove section and the radial-clearance strip extending from the actual opening to the opposing surface. Users must also consider service pressure, extrusion gaps, seal material and compatibility, temperature, lubrication, dynamic duty, installation and other relevant application requirements.

See [Engineering scope and limitations](docs/ENGINEERING_SCOPE.md) and the application's **Settings → Assumptions** and **Settings → References** tabs.

## Project structure

After publication, the repository will include:

| Path | Contents |
|---|---|
| `src/calculations/` | Radial calculations, installation and gland geometry |
| `src/catalog/`, `src/resources/data/` | O-ring catalogue and reference dimensions |
| `src/ui/` | PySide6 interfaces and Qt Designer forms |
| `src/resources/guides/` | The eight Dimension Guides |
| `tests/` | Engineering and interface regression tests |
| `tools/` | Local developer tools and Windows packaging |
| `docs/` | Engineering scope and project documentation |

Proprietary reference publications, private technical drawings, development environments and generated build folders are not part of the public distribution.

## Licence and references

Original application source: **MIT Licence**; see [LICENSE](LICENSE).

Python packages, Qt/PySide6, O-ring reference publications and third-party data or artwork retain their own terms. Engineering reference publications are cited in the application, not redistributed here.
