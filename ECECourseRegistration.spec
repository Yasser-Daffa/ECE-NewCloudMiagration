# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('.env', '.'), ('app_ui', 'app_ui'), ('admin', 'admin'), ('student', 'student'), ('login_files', 'login_files'), ('helper_files', 'helper_files'), ('database_files', 'database_files')]
binaries = []
hiddenimports = ['dotenv', 'dotenv.main', 'python_dotenv', 'psycopg2', 'smtplib', 'email', 'email.mime.text', 'email.mime.multipart', 'ssl', 'socket', 'urllib', 'urllib.request', 'json', 'bcrypt']
tmp_ret = collect_all('psycopg2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('bcrypt')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ECECourseRegistration',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ECECourseRegistration'
)