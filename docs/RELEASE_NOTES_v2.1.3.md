# v2.1.3 - Mixed tolerance keyboard navigation

This maintenance release corrects Tab and Shift+Tab navigation when
symmetrical (+/-) and absolute Min/Max tolerance fields are mixed.

- Symmetrical rows: Nominal, then Tolerance, then the next dimension.
- Limits rows: Minimum, then Maximum, then the next dimension.
- The existing dimension order and application setup controls are preserved.
- Hidden geometry fields and disabled AS568 catalogue fields are skipped.
- Switching between entry modes, gland configurations and resetting dimensions
  requires no manual reconstruction of the focus chain.

All engineering calculations, acceptance criteria, input and snapshot layouts,
tolerance conversion, and the v2.1.2 HTTPS update checker are unchanged.

The Windows portable ZIP contains one unsigned executable. Extract it and
run it without installing Python or a separate runtime. Windows security
policies may restrict unsigned applications.

See [Windows packaging](WINDOWS_PACKAGING.md),
[engineering scope](ENGINEERING_SCOPE.md), and
[Qt rebuild and LGPL guidance](ONEFILE_REBUILD_AND_LGPL.md).

## Verification

- All 304 automated tests passed against the staged public source, including
  forward and reverse navigation across all eight geometry configurations,
  mixed tolerance representations, catalogue selection and reset.
- The Windows single-file build passed the resource and TLS plugin checks.
- ZIP integrity and checksum were verified. The independently extracted EXE
  successfully completed the Settings > Updates check on native Windows.

ZIP SHA-256: `b255b17bc6cc667bb27e1cfa3f7a0950c0ae47571beae6d7c85663dfbeba7515`

Previous release: [v2.1.2](RELEASE_NOTES_v2.1.2.md).
