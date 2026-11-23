# v2.1.2 - Reliable GitHub update checks in portable Windows EXE

This maintenance release repairs **Settings > Updates > Check for updates**,
which could incorrectly report **"Unable to check updates. Try again when
online."** even with a working internet connection.

## Root causes

1. The v2.1.1 checker used GitHub's unauthenticated REST endpoint for the
   latest release. GitHub returned HTTP 403 **API rate limit exceeded**,
   which the application incorrectly described as an offline connection.
2. The v2.1.1 portable EXE included Qt Network but omitted Qt's **native
   Windows Schannel TLS plugin**, making HTTPS unreliable when the machine
   had no compatible external OpenSSL libraries.

## Corrections

- The checker now uses a lightweight HTTPS **HEAD** request to the public
  [Latest release page](https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/latest)
  and reads GitHub's HTTPS redirect to the concrete
  `/releases/tag/vMAJOR.MINOR.PATCH` URL. This route avoids the REST API
  request quota, without needing credentials or retrieving HTML content.
- Results are validated against the repository's precise HTTPS GitHub URL,
  and version numbers are parsed strictly before offering downloads.
- Offline/network errors, HTTP access failures and the absence of any
  published release receive different status messages.
- The single-file Windows builder now **explicitly bundles**
  `qschannelbackend.dll` in Qt's TLS plugin directory and fails the build
  if the plugin is not packaged. The existing unused Virtual Keyboard
  exclusions remain unchanged.
- There are no automatic software downloads or installations, and the
  user's existing opt-in preference for launch-time checks is retained.

## Unchanged

The Detailed/Simplified engineering calculations, geometry, AS568 data,
tolerance conversion, acceptance criteria, application window and snapshot
presentation (including the v2.1.1 50-pixel report-column adjustment)
are unchanged.

## Download and validation

The portable ZIP contains exactly one Windows EXE, with a matching SHA-256
checksum asset. Unzip and run the EXE without a separate installer, Python
runtime or `_internal` directory. The EXE remains unsigned and Windows
SmartScreen/workplace security restrictions may apply.

The released source includes deterministic tests for current, newer,
missing and invalid version redirects, network errors and rate limits.
The public source passed **303 automated regression tests**. The packaged EXE
passed embedded-resource and TLS-backend inventory checks and retained the
unused Qt Virtual Keyboard exclusions. The ZIP was independently extracted;
its checksum and single-EXE contents were verified. On native Windows, the
extracted EXE's actual **Settings > Updates > Check for updates** button
returned **Up to date**, including while anonymous REST API calls from the
same machine were rate-limited.

**Portable ZIP SHA-256:** `c5a96e77da7749fde3480e35a3d62c95b9e9fb9befbba2a8c90b7764444410ae`

For engineering scope and third-party licence obligations, consult
[engineering scope](ENGINEERING_SCOPE.md),
[Windows packaging](WINDOWS_PACKAGING.md),
[one-file rebuild and Qt/LGPL guidance](ONEFILE_REBUILD_AND_LGPL.md) and
[third-party notices](THIRD_PARTY_NOTICES.md).

Previous releases: [v2.1.1](RELEASE_NOTES_v2.1.1.md) and
[v2.1.0](RELEASE_NOTES_v2.1.0.md).
