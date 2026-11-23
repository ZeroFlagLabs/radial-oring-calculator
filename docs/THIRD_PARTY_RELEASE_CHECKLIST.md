# Third-party redistribution checklist — v2.0.0

This is a **technical and licensing preparation record**, not a legal opinion or an assertion that all obligations are discharged.

| Component / resource | Review status |
|---|---|
| Project source and original icon/8 Dimension Guides | Project-owner-created, approved for public distribution. |
| AS568 349-record reference-data compilation | Project owner confirms they have redistribution permission. Attribution preserved in the JSON; underlying manufacturer publications/standards are not included or licensed by this statement. |
| Six small application UI glyphs | Created for this application and cleared for redistribution by the project owner. |
| PySide6, PySide6 Essentials and Addons, shiboken6 6.12.0 | Matching-version Qt and PySide6 source archives with SHA-256 checksums are attached to the v1.0.0 Release. The tagged repository provides LGPL/GPL texts, matching-source information and rebuilding/relinking instructions; the v2 ZIP contains one EXE only. |
| GPL-only Qt Virtual Keyboard | Two unnecessary DLL/plugin binaries explicitly excluded from the v2.0.0 PyInstaller archive; packaged inventory checks passed. |
| Python 3.13.16, Windows runtimes, PyInstaller 6.22.3 bootloader | Python and PyInstaller/runtime licence guidance retained in the tagged repository and earlier companion licensing resources; applicable Microsoft runtime terms remain separate. |
| Qt third-party components (such as image codecs/OpenSSL) | The tagged repository provides third-party notices and Qt references. Additional component-level attributions, OpenSSL licence material and matching-source references were supplied with the earlier v1.0.0 companion licensing resources. |
| Proprietary reference guides, private CAD/models | Excluded from source and portable release. |

## Qt LGPL publication requirement

The v2.0.0 one-file EXE extracts Qt DLLs at runtime; users may rebuild the application with compatible modified Qt/PySide6 libraries as described in the tagged source. **That rebuilding route does not by itself settle all LGPLv3 obligations**. Include LGPLv3/GPLv3 texts; a genuine complete-corresponding-source delivery or valid written offer under distributor control; any required Qt third-party notices; and a clear, usable explanation of how recipients can replace compatible libraries. Review [Qt's guidance](https://www.qt.io/development/open-source-lgpl-obligations) and [Qt's third-party licence listing](https://doc.qt.io/qt-6/licenses-used-in-qt.html).

The v1.0.0 release supplies the identified matching-version Qt/PySide6 source archives under the distributor's release assets, together with appropriate checksum references. The tagged repository documents compatible-library rebuilding/replacement and provides third-party notices; the v2 ZIP contains one EXE only. This checklist is a technical release record, not a legal opinion; check applicable individual component terms with a qualified adviser if necessary. The MIT-licensed application source remains separate from the third-party libraries.
