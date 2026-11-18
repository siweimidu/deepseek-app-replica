"""Wire the pointer-capture swipe into App and give the animation a springy feel."""

import re
from pathlib import Path

# 1) hook 里补回"打开即进度 1"的不变量
HOOK = Path('src/components/sider/useDrawerSwipe.ts')
hook = HOOK.read_text(encoding='utf-8')
hook = hook.replace(
    "import { useCallback, useRef } from 'react'",
    "import { useCallback, useEffect, useRef } from 'react'",
    1,
)
if 'useMobileSider.subscribe' not in hook:
    hook = hook.rstrip() + """

/** 不变量：打开 ⇒ 进度恒为 1；关闭 ⇒ 不留内联进度。拖拽中不干预。 */
useEffectSafe(frameRef)

function useEffectSafe(frameRef: { current: HTMLElement | null }) {
  // 单独抽出来只是为了让上面的 hook 保持整洁
  return useMobileInvariant(frameRef)
}

function useMobileInvariant(frameRef: { current: HTMLElement | null }) {
  useEffect(
    () =>
      useMobileSider.subscribe((state) => {
        const frame = frameRef.current
        if (!frame || frame.hasAttribute('data-drawer-dragging')) {
          return
        }
        if (state.open) {
          frame.style.setProperty('--drawer-progress', '1')
        } else {
          frame.style.removeProperty('--drawer-progress')
        }
      }),
    [frameRef],
  )
}
"""
HOOK.write_text(hook, encoding='utf-8')
print('invariant restored')

# 2) App：把返回的处理函数铺到 frame 上
APP = Path('src/app/App.tsx')
app = APP.read_text(encoding='utf-8')
app = app.replace(
    "  useDrawerSwipe(frameRef)\n",
    "  const drawerSwipe = useDrawerSwipe(frameRef)\n",
    1,
)
if '{...drawerSwipe}' not in app:
    app = app.replace(
        "        data-drawer-open={drawerOpen}\n",
        "        data-drawer-open={drawerOpen}\n        {...drawerSwipe}\n",
        1,
    )
APP.write_text(app, encoding='utf-8')
print('handlers spread on frame')

# 3) 动画：抽屉用带轻微过冲的弹簧曲线，卡片稍慢一点形成层次
MOTION = Path('src/app/motion.css')
motion = MOTION.read_text(encoding='utf-8')
motion = re.sub(
    r"--motion-drawer:\s*\n?\s*[^;]+;",
    "--motion-drawer:\n    300ms linear(0, 0.18 6%, 0.52 16%, 0.82 28%, 0.98 42%, 1.028 58%, 1.012 74%, 0.998 88%, 1);",
    motion,
)
MOTION.write_text(motion, encoding='utf-8')
print('springy drawer curve')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 40', gradle), encoding='utf-8')
print('versionCode 40')
