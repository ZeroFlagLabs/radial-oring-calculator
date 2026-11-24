# v2.1.4 - Partial dimensional limits

Improved tolerance mode conversion for partially entered dimensional limits,
allowing users to return to symmetrical tolerance mode without losing the
populated dimension.

- For positive-only diameters, groove depths, groove width and O-ring
  dimensions, one zero endpoint and one positive endpoint convert to the
  positive nominal with zero tolerance when switching to +/-.
- Both zero endpoints and equal non-zero limits retain their usual meaning.
- Reversed non-zero limits remain invalid. Radii and both angle fields
  retain literal zero endpoints, including signed wall angles.
- The conversion is explicit; calculations and validation in Limits mode
  are unchanged, as are precision checks, navigation and report layout.

The Windows portable ZIP contains one unsigned executable. Extract it and
run it without installing Python or a separate runtime. Windows security
policies may restrict unsigned applications.

See [Windows packaging](WINDOWS_PACKAGING.md),
[engineering scope](ENGINEERING_SCOPE.md), and
[Qt rebuild and LGPL guidance](ONEFILE_REBUILD_AND_LGPL.md).

## Verification

- All 308 automated regression tests passed, including all 13 positive-only
  rows, literal zero endpoints, conversion precision and mixed keyboard navigation.
- Native Windows tests and the independently extracted portable EXE confirmed
  the corrected conversion, representative calculation and keyboard navigation.
- Identical sample inputs produced byte-identical PNG exports from the
  application rendering path in v2.1.3 and v2.1.4.
- Embedded resources, TLS plugin, ZIP integrity and live packaged update
  checking passed.

ZIP SHA-256: `d6847dc339671ab16bc97e86f778b0cb1ec963de23c7ef7cef9bedb9272a83f5`

Previous release: [v2.1.3](RELEASE_NOTES_v2.1.3.md).
