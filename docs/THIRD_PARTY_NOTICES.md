# Third-party notices — Static & Dynamic Radial O-Ring Calculator v1.0.0

**Publisher:** ZeroFlagLabs

**Repository:** https://github.com/ZeroFlagLabs/radial-oring-calculator

## Project code, documentation and original artwork

Original calculator code and documentation are under [MIT](../LICENSE). The eight Dimension Guides and the final application icon were created specifically for the project, as confirmed by the project owner. Third-party components retain their own licences.

## Qt and PySide6

Built using **PySide6 6.12.0**, **PySide6-Essentials 6.12.0**, **PySide6-Addons 6.12.0**, **shiboken6 6.12.0**, and Qt 6.12 libraries/plugins. Copyright The Qt Company Ltd., the Qt Project and their contributors, as applicable. Open-source PySide6 and many Qt libraries are under LGPLv3 (or available under alternative licence terms). Certain other Qt modules have different terms.

The approved one-folder candidate excludes the two unnecessary Qt Virtual Keyboard binaries identified in the v1.0.0 audit. The bundled Qt libraries remain independently licensed. Their recipients retain applicable LGPL rights, including modification and replacement of compatible dynamic libraries. The LGPLv3 and GPLv3 texts are provided under `licenses/`; this does not alone discharge every LGPL requirement.

Matching Qt 6.12.0 and PySide6/Shiboken6 6.12.0 source archives are provided as distributor-hosted companion assets on the [v1.0.0 GitHub Release](https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/tag/v1.0.0), together with SHA-256 checksums. The Windows ZIP includes `QT_SOURCE_AND_REPLACEMENT.md` describing how recipients can replace compatible Qt/PySide6 libraries. The source archives are **not** required to run the application. See [licensing checklist](THIRD_PARTY_RELEASE_CHECKLIST.md).

Qt references: https://doc.qt.io/qt-6/licensing.html ; https://doc.qt.io/qt-6/licenses-used-in-qt.html ; https://doc.qt.io/qtforpython-6/licenses.html ; https://www.qt.io/development/open-source-lgpl-obligations

## Python and PyInstaller

The frozen Windows binary embeds the Python **3.13.16** runtime, licensed under the Python Software Foundation License and applicable bundled-component licences: https://docs.python.org/3/license.html . The executable was built with **PyInstaller 6.22.3**, whose bootloader licensing exception permits distribution under the application licence subject to third-party compliance: https://pyinstaller.org/en/v6.22.3/license.html . Windows runtime components are supplied under their respective terms.

## AS568 catalogue

`src/resources/data/as568_reference.json` includes 349 reference sizes with nominal ID, cross-section and tolerances. Its metadata identifies transcription/cross-check sources, including Apple Rubber, Freudenberg and Parker. The project owner confirms permission to redistribute the catalogue compilation. This permission statement does **not** cover the source manufacturer publications, drawings, text, or underlying standards, which are not redistributed.

## Other notices

The Windows ZIP includes `THIRD_PARTY_COMPONENTS.md`, which documents the shipped Qt module/plugin families and references Qt's version-specific third-party attribution index and the corresponding-source archives. It also includes applicable licence texts for LGPLv3, GPLv3, Python and OpenSSL. Individual bundled components retain their own licences, and this notice is not a legal clearance certificate.
