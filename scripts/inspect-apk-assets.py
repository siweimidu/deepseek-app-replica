"""Inspect the shipped APK: web assets present/valid, native markers intact."""

import json
import zipfile
from pathlib import Path

APK = r'C:\Users\35238\Documents\deepseek-harness\default-workspace\out\DeepSleep-0.1.0-build59.apk'
z = zipfile.ZipFile(APK)

names = z.namelist()
assets = [n for n in names if n.startswith('assets/')]
print('assets count:', len(assets))
print('index.html present:', 'assets/index.html' in names)
idx = z.read('assets/index.html').decode('utf-8', 'ignore')
js = [n for n in names if n.startswith('assets/static/js/main')]
print('js bundles:', js)
print('index.html length:', len(idx))
print('index references js:', js[0].replace('assets/', '') in idx)

bundle = z.read(js[0]) if js else b''
print('bundle size:', len(bundle))
for marker in [b'androidSelectChats', b'selectChats', b'touchSlop', b'onPointerDownCapture', b'__dshSwipe']:
    print(f'  {marker.decode()}:', marker in bundle)

dex = z.read('classes.dex')
for marker in [b'dispatchTouchEvent', b'handleBack', b'__dshSwipe']:
    print(f'  dex {marker.decode()}:', marker in dex)

# css 是否被打进 js（rspack 默认注入 style）
print('has css in bundle:', b'selectChats' in bundle)
