"""把横滑换回 build47 的实现（方向无关、touch 抢手势、可双向切换）。"""

import re
import subprocess
from pathlib import Path

ROOT = Path('.')

# 1) 取回 build47 的 hook
content = subprocess.run(
    ['git', 'show', '6e91eab:src/components/sider/useDrawerSwipe.ts'],
    capture_output=True,
    check=True,
).stdout.decode('utf-8')
Path('src/components/sider/useDrawerSwipe.ts').write_text(content, encoding='utf-8')
print('build47 hook restored:', len(content.splitlines()), 'lines')

# 2) App 接线改回 useDrawerSwipe(frameRef)
APP = ROOT / 'src/app/App.tsx'
app = APP.read_text(encoding='utf-8')
app = app.replace(
    "import { useAndroidDrawerGesture } from '../components/sider/useAndroidDrawerGesture.js'",
    "import { useDrawerSwipe } from '../components/sider/useDrawerSwipe.js'",
)
app = app.replace(
    "  const drawerGesture = useAndroidDrawerGesture()\n",
    "  useDrawerSwipe(frameRef)\n",
)
app = app.replace("        {...(android && isMobile ? drawerGesture : {})}\n", '')
APP.write_text(app, encoding='utf-8')
print('App wired to build47 hook:', 'useDrawerSwipe(frameRef)' in app and 'drawerGesture' not in app)

# 3) 删掉上游 hook
upstream = ROOT / 'src/components/sider/useAndroidDrawerGesture.ts'
if upstream.exists():
    upstream.unlink()
    print('upstream hook removed')

GRADLE = ROOT / 'android/app/build.gradle'
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 63', gradle), encoding='utf-8')
print('versionCode 63')
