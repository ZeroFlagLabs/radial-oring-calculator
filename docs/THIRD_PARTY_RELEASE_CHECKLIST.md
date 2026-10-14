# Third-party redistribution checklist — v1.0.0

This is a **technical and licensing preparation record**, not a legal opinion or an assertion that all obligations are discharged.

| Component / resource | Review status |
|---|---|
| Project source and original icon/8 Dimension Guides | Project-owner-created, approved for public distribution. |
| AS568 349-record reference-data compilation | Project owner confirms they have redistribution permission. Attribution preserved in the JSON; underlying manufacturer publications/standards are not included or licensed by this statement. |
| Six small application UI glyphs | Created for this application and cleared for redistribution by the project owner. |
| PySide6, PySide6 Essentials and Addons, shiboken6 6.12.0 | Matching-version Qt and PySide6 source archives with SHA-256 checksums are attached to the v1.0.0 Release. The Windows ZIP supplies LGPL/GPL texts and library-replacement instructions. |
| GPL-only Qt Virtual Keyboard | Two unnecessary audited DLL/plugin binaries **excluded** from the clean 110-binary Windows candidate, which passed a standalone smoke test. |
| Python 3.13.16, Windows runtimes, PyInstaller 6.22.3 bootloader | Python licence and PyInstaller/runtime attribution guidance included in the Windows ZIP, with applicable Microsoft runtime terms preserved. |
| Qt third-party components (such as image codecs/OpenSSL) | The Windows ZIP includes `THIRD_PARTY_COMPONENTS.md`, OpenSSL licence text, and links to Qt 6.12.0 component-level attributions and matching source archives. |
| Proprietary reference guides, private CAD/models | Excluded from source and portable release. |

## Qt LGPL publication requirement

The one-folder archive allows users to replace compatible Qt DLLs, but **that alone does not meet all LGPLv3 terms**. Include LGPLv3/GPLv3 texts; a genuine complete-corresponding-source delivery or valid written offer under distributor control; any required Qt third-party notices; and a clear, usable explanation of how recipients can replace compatible libraries. Review [Qt's guidance](https://www.qt.io/development/open-source-lgpl-obligations) and [Qt's third-party licence listing](https://doc.qt.io/qt-6/licenses-used-in-qt.html).

The v1.0.0 release supplies the identified matching-version Qt/PySide6 source archives under the distributor's release assets, together with appropriate checksum references. The Windows ZIP documents compatible-library replacement and includes third-party notices. This checklist is a technical release record, not a legal opinion; check applicable individual component terms with a qualified adviser if necessary. The MIT-licensed application source remains separate from the third-party libraries.
