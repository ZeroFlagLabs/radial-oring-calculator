# Third-party redistribution checklist — v1.0.0

This is a **technical and licensing preparation record**, not a legal opinion or an assertion that all obligations are discharged.

| Component / resource | Review status |
|---|---|
| Project source and original icon/8 Dimension Guides | Project-owner-created, approved for public distribution. |
| AS568 349-record reference-data compilation | Project owner confirms they have redistribution permission. Attribution preserved in the JSON; underlying manufacturer publications/standards are not included or licensed by this statement. |
| Six small application UI glyphs | Contained in audited app source. Confirm the same ownership/terms before final public push if any are third-party. |
| PySide6, PySide6 Essentials and Addons, shiboken6 6.12.0 | Open-source Qt/PySide6 terms and notices identified. **Corresponding Qt/PySide6 source access/offer, component notices and library-replacement instructions must be in place before publishing binary.** |
| GPL-only Qt Virtual Keyboard | Two unnecessary audited DLL/plugin binaries **excluded** from the clean 110-binary Windows candidate, which passed a standalone smoke test. |
| Python 3.13.16, Windows runtimes, PyInstaller 6.22.3 bootloader | Include applicable Python, runtime and PyInstaller notices/attributions based on shipped binary inventory. |
| Qt third-party components (such as image codecs/OpenSSL) | Check exact final binary distribution against Qt's 6.12 third-party licence/SBOM records. |
| Proprietary reference guides, private CAD/models | Excluded from source and portable release. |

## Qt LGPL publication requirement

The one-folder archive allows users to replace compatible Qt DLLs, but **that alone does not meet all LGPLv3 terms**. Include LGPLv3/GPLv3 texts; a genuine complete-corresponding-source delivery or valid written offer under distributor control; any required Qt third-party notices; and a clear, usable explanation of how recipients can replace compatible libraries. Review [Qt's guidance](https://www.qt.io/development/open-source-lgpl-obligations) and [Qt's third-party licence listing](https://doc.qt.io/qt-6/licenses-used-in-qt.html).

**Do not state that the source arrangement is complete until it actually is.** Verify with an appropriate licensing adviser if uncertain. The source code under the MIT licence is distinct from the third-party libraries included in the binary.
