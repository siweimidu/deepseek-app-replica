"""Verify the built APK actually contains the native swipe code and the JS bridge."""

import re
import zipfile
from pathlib import Path

gradle = Path('android/app/build.gradle')
gradle.write_text(re.sub(r'versionCode = \d+', 'versionCode = 45', gradle.read_text(encoding='utf-8')), encoding='utf-8')
print('versionCode 45 set')

z = zipfile.ZipFile(r'android/app/build/outputs/apk/release/app-release.apk')
dex = z.read('classes.dex')
print('native dispatchSwipeIfHorizontal in dex:', b'dispatchSwipeIfHorizontal' in dex)
print('native __dshSwipe call in dex:', b'__dshSwipe' in dex)
js = [n for n in z.namelist() if n.startswith('assets/static/js/main')][0]
bundle = z.read(js)
print('js __dshSwipe bridge in bundle:', b'__dshSwipe' in bundle)
