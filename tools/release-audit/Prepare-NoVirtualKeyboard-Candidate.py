#!/usr/bin/env python3
"""Safely copy a tested PyInstaller one-folder build, excluding unused GPL-only Qt Virtual Keyboard.

PREVIEW by default. The original project, source, dist folder and GitHub remain untouched.
Requires the adjacent original BUNDLED_BINARY_MANIFEST.csv produced by the v1.0.0 review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime
from pathlib import Path, PurePosixPath
import shutil
import sys

APP = "Static & Dynamic Radial O-Ring Calculator v1.0.0"
EXCLUSIONS = {
    "_internal/PySide6/Qt6VirtualKeyboard.dll": "973369caa6d13fa08f6b1cd57004dcf4f137f8ef98ec6876ad07ba690ee0b9a3",
    "_internal/PySide6/plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll": "bbf479e6380061699e734a32f4fe0b6fc8bc2de007ae53b0206e6e36abf1e3e2",
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def read_manifest(path: Path) -> dict[str, tuple[int,str]]:
    if not path.is_file():
        raise ValueError(f"Cannot find bundle manifest: {path}")
    items = {}
    with path.open(newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            key = row["relative_to_distribution"]
            pure = PurePosixPath(key)
            if pure.is_absolute() or ".." in pure.parts or "\\" in key or not pure.parts:
                raise ValueError(f"Unsafe manifest path: {key}")
            if key in items:
                raise ValueError(f"Duplicate manifest path: {key}")
            items[key] = (int(row["bytes"]), row["sha256"].lower())
    if len(items) != 112:
        raise ValueError(f"Expected 112 binary entries; found {len(items)}. New review required.")
    for name, expected_hash in EXCLUSIONS.items():
        if items.get(name, (None, None))[1] != expected_hash:
            raise ValueError(f"Virtual Keyboard component has changed since audit: {name}")
    return items

def check(directory: Path, entries: dict[str, tuple[int, str]], omitted: set[str] | None = None) -> None:
    """Verify the ORIGINAL as-is, or a copied candidate with `omitted` absent.

    The original contains the two specifically audited Virtual Keyboard files;
    they must be present and hash-verified before a separate copy is made.
    """
    omitted = omitted or set()
    for rel, (size, expected_hash) in entries.items():
        path = directory.joinpath(*PurePosixPath(rel).parts)
        if rel in omitted:
            if path.exists():
                raise ValueError(f"Excluded Virtual Keyboard file remains in clean copy: {path}")
            continue
        if not path.is_file():
            raise ValueError(f"Bundled file missing: {path}")
        if path.stat().st_size != size or sha256(path) != expected_hash:
            raise ValueError(f"Bundled file hash/size mismatch: {path}")

    # Reject other, unreviewed Virtual Keyboard binaries in either copy.
    # In the *original*, the two audited files are expected and are verified above.
    # In the *clean copy*, no Virtual Keyboard components should remain.
    permitted = set(EXCLUSIONS) - omitted
    for path in directory.rglob('*'):
        if path.is_file() and 'virtualkeyboard' in path.name.lower():
            relative = path.relative_to(directory).as_posix()
            if relative not in permitted:
                raise ValueError(f"Unexpected Virtual Keyboard component: {path}")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path, help='Existing Windows project root')
    parser.add_argument('--manifest', type=Path,
        default=Path(__file__).resolve().with_name('BUNDLED_BINARY_MANIFEST.csv'))
    parser.add_argument('--output-root', type=Path, default=Path.home() / 'Downloads')
    parser.add_argument('--apply', action='store_true', help='Make a new, separate copy and remove two identified binaries')
    a = parser.parse_args()
    source = a.project.resolve() / 'dist' / APP
    if not source.is_dir():
        raise ValueError(f"One-folder build not found: {source}")
    entries = read_manifest(a.manifest)
    print(f"Existing tested build: {source}")
    print(f"Checking all {len(entries)} binary files against publication-review manifest...")
    check(source, entries)
    print('Original bundle hashes: VERIFIED')
    print('Unused Qt Virtual Keyboard binaries to omit:')
    for name in EXCLUSIONS: print(' -', name)
    if not a.apply:
        print('PREVIEW ONLY. No files copied, changed or deleted. Add --apply to prepare the separate copy.')
        return 0
    out = a.output_root.expanduser().resolve()
    if not out.is_dir(): raise ValueError(f"Output root does not exist: {out}")
    if out == source or source in out.parents:
        raise ValueError("Output root must not be inside the original distribution folder")
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    candidate_root = out / f'Radial_ORing_NoVirtualKeyboard_Candidate_{stamp}'
    destination = candidate_root / APP
    if candidate_root.exists(): raise ValueError(f"Already exists: {candidate_root}")
    try:
        shutil.copytree(source, destination)
        for rel, expected in EXCLUSIONS.items():
            path = destination.joinpath(*PurePosixPath(rel).parts)
            if sha256(path) != expected:
                raise ValueError(f"Refusing to remove altered binary: {path}")
            path.unlink()  # Only in NEW separate copy; original source not touched.
        check(destination, entries, omitted=set(EXCLUSIONS))
        (candidate_root/'READ_ME_FIRST.txt').write_text(
            'DISTRIBUTION CANDIDATE ONLY - NOT YET LICENCE CLEARED OR PUBLISHED.\n'
            'Two unused GPL-only Qt Virtual Keyboard components excluded.\n'
            'This does not itself complete Qt/PySide6 LGPLv3 compliance.\n'
            'Do not redistribute until Qt source availability, required notices and licences are resolved.\n'
            'Test the application EXE within the folder, and keep _internal alongside it.\n',encoding='utf-8')
    except Exception:
        print('ERROR preparing separate candidate; original tested distribution is unaffected.',file=sys.stderr)
        print(f'If a partial folder was created, inspect/remove it manually: {candidate_root}',file=sys.stderr)
        raise
    print('PREPARED: clean separate candidate; all 110 remaining binary hashes verified.')
    print('Location:', destination)
    print('Launch:', destination / (APP + '.exe'))
    print('No original files, Git history or GitHub releases have been modified.')
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        raise SystemExit(1)
