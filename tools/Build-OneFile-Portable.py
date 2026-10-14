#!/usr/bin/env python3
"""Build a single-file Windows EXE from the CURRENT public ZeroFlagLabs source.

Required: Windows 11, Python 3.13, PyInstaller 6.22.3, PySide6 6.12.0;
invoke using that environment's Python. No source files are modified.
For Qt LGPL relinking, install compatible rebuilt Qt/PySide6 DLLs into the build
Python environment before running this script. See docs/ONEFILE_REBUILD_AND_LGPL.md.
"""
from pathlib import Path
import argparse
import hashlib
import os
import re
import subprocess
import sys
import zipfile

DATA = (
    ('src/ui/forms/main_window.ui', 'src/ui/forms'),
    ('src/ui/forms/settings_dialog.ui', 'src/ui/forms'),
    ('src/ui/forms/inspect_results.ui', 'src/ui/forms'),
    ('src/resources/data/as568_reference.json', 'src/resources/data'),
    ('src/resources/guides', 'src/resources/guides'),
    ('src/resources/icons', 'src/resources/icons'),
)
BLOCKED = ('qt6virtualkeyboard.dll', 'qtvirtualkeyboardplugin.dll')
GUIDES = ('cylinder_dovetail_depth.png','cylinder_dovetail_id.png',
          'cylinder_rectangular_depth.png','cylinder_rectangular_id.png',
          'piston_dovetail_depth.png','piston_dovetail_od.png',
          'piston_rectangular_depth.png','piston_rectangular_od.png')

def run(cmd, cwd, capture=False):
    result = subprocess.run([str(s) for s in cmd], cwd=str(cwd), check=True,
                            text=True, stdout=subprocess.PIPE if capture else None)
    return result.stdout if capture else ''

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def main():
    if os.name != 'nt':
        raise RuntimeError('Build this Windows EXE on Windows.')
    p = argparse.ArgumentParser()
    p.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--output', type=Path, default=None)
    a = p.parse_args()
    root = a.project.resolve(strict=True)
    dest = (a.output or (root / 'dist-onefile')).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    info = (root / 'src/app_info.py').read_text(encoding='utf8')
    title = re.search(r"^APP_TITLE = '([^']+)'$", info, re.M)
    version = re.search(r"^APP_VERSION = '([^']+)'$", info, re.M)
    if not title or not version:
        raise RuntimeError('Missing APP_TITLE / APP_VERSION in app_info.py')
    name = f'{title.group(1)} v{version.group(1)}'
    if any(c in name for c in '\\/:*?"<>|'):
        raise RuntimeError('Invalid EXE name.')
    icon = root / 'src/resources/icons/icon.ico'
    if not icon.is_file():
        raise RuntimeError('Missing application icon.')
    if any(not (root/'src/resources/guides'/g).is_file() for g in GUIDES):
        raise RuntimeError('Missing one or more Dimension Guides.')
    for src, _ in DATA:
        if not (root / src).exists():
            raise RuntimeError('Missing application resource: ' + src)
    print('PyInstaller:', run([sys.executable, '-m', 'PyInstaller', '--version'], root, True).strip())
    import shutil
    maker = shutil.which('pyi-makespec', path=str(Path(sys.executable).parent))
    if maker is None:
        raise RuntimeError('pyi-makespec not found beside selected Python environment.')
    specdir, workdir, distdir = (dest/'spec', dest/'work', dest/'exe')
    for d in (specdir, workdir, distdir):
        d.mkdir(parents=True, exist_ok=True)
    cmd = [maker, '--onefile', '--windowed', '--name', name,
           '--paths', root, '--specpath', specdir, '--icon', icon]
    for src, target in DATA:
        cmd += ['--add-data', str(root/src)+';'+target]
    if (root/'src/resources/images').is_dir():
        cmd += ['--add-data', str(root/'src/resources/images')+';src/resources/images']
    cmd.append(root/'src/main.py')
    run(cmd, root)
    spec = specdir / (name+'.spec')
    txt = spec.read_text(encoding='utf8')
    m = list(re.finditer(r'^pyz\s*=\s*PYZ\(', txt, re.M))
    if len(m) != 1:
        raise RuntimeError('Unexpected PyInstaller spec format.')
    patch = """# Remove unneeded GPL-only Virtual Keyboard files after analysis.
_blocked = {'qt6virtualkeyboard.dll','qtvirtualkeyboardplugin.dll'}
_removed = []
for _attr in ('binaries', 'datas'):
    _kept = []
    for _entry in getattr(a, _attr):
        _base = _entry[0].replace('\\\\', '/').rsplit('/',1)[-1].lower()
        if _base in _blocked:
            _removed.append((_attr, _entry[0]))
        else:
            _kept.append(_entry)
    setattr(a, _attr, _kept)
if set(x[1].replace('\\\\','/').rsplit('/',1)[-1].lower() for x in _removed) != _blocked:
    raise RuntimeError('Expected exactly two Virtual Keyboard components to remove: ' + repr(_removed))
print('Excluded Qt Virtual Keyboard files:', _removed, flush=True)

"""
    patched = txt[:m[0].start()]+patch+txt[m[0].start():]
    compile(patched, str(spec), 'exec')
    spec.write_text(patched, encoding='utf8')
    run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
         '--workpath', workdir, '--distpath', distdir, spec], root)
    exe = distdir/(name+'.exe')
    if not exe.is_file():
        raise RuntimeError('Missing generated EXE.')
    listing = run([sys.executable, '-m', 'PyInstaller.utils.cliutils.archive_viewer',
                   '--list', '--recursive', '--brief', exe], root, True).lower()
    if any(s in listing for s in BLOCKED):
        raise RuntimeError('GPL-only Virtual Keyboard component still present.')
    for s in (*GUIDES,'main_window.ui','settings_dialog.ui','inspect_results.ui',
              'as568_reference.json','settings-gear.png','app-icon.png'):
        if s.lower() not in listing:
            raise RuntimeError('Missing resource from built EXE: ' + s)
    zippath = dest/(f'Radial-ORing-Calculator-v{version.group(1)}-Windows-Portable.zip')
    if zippath.exists():
        raise RuntimeError('Refusing to overwrite prior release archive: ' + str(zippath))
    with zipfile.ZipFile(zippath,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.write(exe, exe.name)
    with zipfile.ZipFile(zippath) as z:
        if z.testzip() is not None or z.namelist()!=[exe.name]:
            raise RuntimeError('ZIP contains more than one EXE or is damaged.')
    digest=sha256(zippath)
    (dest/(zippath.name+'.sha256')).write_text(digest+'  '+zippath.name+'\n',encoding='ascii')
    print('ONE-FILE BUILD SUCCESSFUL:',exe)
    print('ZIP:',zippath)
    print('SHA-256:',digest)

if __name__ == '__main__':
    main()
