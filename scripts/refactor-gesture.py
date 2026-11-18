"""Replace the multi-handler drawer gesture with the single touch state machine."""

import re
from pathlib import Path

SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')

# 1) 去掉抽屉上的全部手势属性，只留 onClickCapture 防拖拽误点
start = sider.index("        onTouchStart={(event) => {")
end = sider.index("        onClickCapture={(event) => {", start)
sider = sider[:start] + sider[end:]

# dragged 现在由新钩子维护不到点击层，点击不再需要抑制
sider = sider.replace(
    """        onClickCapture={(event) => {
          // 刚拖动过就不要把这次手势当成点击
          if (dragged.current) {
            event.preventDefault()
            event.stopPropagation()
          }
        }}
""",
    "",
    1,
)

# 2) 清掉不再使用的拖动相关代码
for pattern in [
    r"  const drag = useRef<\{ x: number; y: number; width: number; horizontal: boolean \} \| null>\(null\)\n",
    r"  const dragged = useRef\(false\)\n",
    r"  const closeSwipe = useRef<\{ x: number; y: number; armed: boolean \} \| null>\(null\)\n",
    r"  const touchSwipe = useRef<\{ x: number; y: number \} \| null>\(null\)\n",
]:
    sider = re.sub(pattern, '', sider)

# setProgress / releaseDrag / settle 三个辅助函数整段删除
for name in ['setProgress', 'releaseDrag', 'settle']:
    match = re.search(rf"\n  /\*\*[^\n]*\*/\n  const {name} = [\s\S]*?\n  \}}\n", sider)
    if match:
        sider = sider[: match.start()] + '\n' + sider[match.end() :]
    else:
        match = re.search(rf"\n  const {name} = [\s\S]*?\n  \}}\n", sider)
        if match:
            sider = sider[: match.start()] + '\n' + sider[match.end() :]

SIDER.write_text(sider, encoding='utf-8')
print('drawer gesture handlers removed')

# 3) App：改用单一的触摸状态机
APP = Path('src/app/App.tsx')
app = APP.read_text(encoding='utf-8')
app = app.replace(
    "import { useAndroidDrawerGesture } from '../components/sider/useAndroidDrawerGesture.js'",
    "import { useDrawerSwipe } from '../components/sider/useDrawerSwipe.js'",
    1,
)
app = app.replace(
    "  const drawerGesture = useAndroidDrawerGesture()\n",
    "  const frameRef = useRef<HTMLDivElement>(null)\n  useDrawerSwipe(frameRef)\n",
    1,
)
app = app.replace(
    "        {...(android ? drawerGesture : {})}\n",
    "",
    1,
)
app = app.replace(
    "      className={styles.frame}\n",
    "      className={styles.frame}\n      ref={frameRef}\n",
    1,
)
if 'useRef' not in app.split('\n')[0] and 'useRef' not in app[:400]:
    app = app.replace(
        "import { useEffect } from 'react'",
        "import { useEffect, useRef } from 'react'",
        1,
    )
APP.write_text(app, encoding='utf-8')
print('App uses the touch state machine')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 32', gradle), encoding='utf-8')
print('versionCode 32')
