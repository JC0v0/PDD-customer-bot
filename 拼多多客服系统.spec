# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('e:\\拼多多后台\\拼多多AI客服--测试\\config\\account_cookies.json', 'config'), ('e:\\拼多多后台\\拼多多AI客服--测试\\config\\account_status.json', 'config'), ('e:\\拼多多后台\\拼多多AI客服--测试\\config.py', '.'), ('e:\\拼多多后台\\拼多多AI客服--测试\\icon', 'icon'), ('E:\\拼多多后台\\拼多多AI客服--测试\\.venv\\Lib\\site-packages\\selenium_stealth\\js', 'selenium_stealth/js')]
binaries = []
hiddenimports = ['config', 'selenium', 'selenium_stealth']
tmp_ret = collect_all('selenium_stealth')
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
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('v', None, 'OPTION')],
    name='拼多多客服系统',
    debug=True,
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
    icon=['PddWorkbench.ico'],
)
