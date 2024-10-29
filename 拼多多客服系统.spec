# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('c:\\Users\\Administrator\\Desktop\\拼多多AI客服--发行版\\config\\account_cookies.json', 'config'), ('c:\\Users\\Administrator\\Desktop\\拼多多AI客服--发行版\\config\\account_status.json', 'config'), ('c:\\Users\\Administrator\\Desktop\\拼多多AI客服--发行版\\config.py', '.'), ('c:\\Users\\Administrator\\Desktop\\拼多多AI客服--发行版\\icon', 'icon'), ('C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\selenium_stealth\\js', 'selenium_stealth/js')]
binaries = [('c:\\Users\\Administrator\\Desktop\\拼多多AI客服--发行版\\chromedriver-win64\\chromedriver.exe', 'chromedriver-win64')]
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
