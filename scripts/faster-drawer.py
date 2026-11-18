"""去掉动画期间最贵的光栅化成本，并把抽屉动画提速到 240ms 的弹跳曲线。"""

import re
from pathlib import Path

# ---------- 1) 更快的弹簧：240ms，约 5% 过冲（快且有弹性） ----------
MOTION = Path('src/app/motion.css')
motion = MOTION.read_text(encoding='utf-8')

FAST = (
    "linear(0, 0.211 17%, 0.569 33%, 0.85 50%, 1.003 67%, 1.056 83%, 1.02 92%, 1.004 97%, 1)"
)
CARD = "linear(0, 0.18 17%, 0.52 33%, 0.82 50%, 0.99 67%, 1.04 83%, 1.012 92%, 1.003 97%, 1)"

motion = re.sub(r"--motion-drawer:\s*\n?\s*[^;]+;", f"--motion-drawer: 240ms {FAST};", motion)
motion = re.sub(r"--motion-card:\s*\n?\s*[^;]+;", f"--motion-card: 260ms {CARD};", motion)
MOTION.write_text(motion, encoding='utf-8')
print('tokens: drawer 240ms / card 260ms with bounce')

# ---------- 2) 动画期间卸掉裁剪与投影（真机上最贵的两项） ----------
APP = Path('src/app/App.module.css')
app = APP.read_text(encoding='utf-8')

if 'data-drawer-animating' not in app:
    app += """
/*
 * 动画期间：不做 overflow 裁剪、不画投影。
 * 全屏元素每帧裁剪 + 16px 模糊投影是弱机光栅化的主要成本；
 * 圆角保留（只是自身背景圆角，不裁剪子节点），动画结束再补回裁剪与投影。
 */
[data-android] .frame[data-drawer-animating] .main {
  overflow: visible;
  box-shadow: none;
}

/* 抽屉本身在动画期间单独成层，避免内容重新光栅化 */
[data-android] .frame[data-drawer-animating] .drawer {
  will-change: transform;
}
"""
    APP.write_text(app, encoding='utf-8')
    print('animation-time raster relief added')

# ---------- 3) JS：状态切换时挂 data-drawer-animating，动画结束撤掉 ----------
HOOK = Path('src/components/sider/useDrawerSwipe.ts')
hook = HOOK.read_text(encoding='utf-8')

OLD = """    const settle = (close: boolean) => {
      release()
      if (close) {
        closeMobileSider()
      } else {
        openMobileSider()
      }
      lastToggleAt.current = Date.now()
      frame.style.removeProperty('--drawer-progress')
      window.setTimeout(() => frame.style.removeProperty('will-change'), 420)"""
NEW = """    const settle = (close: boolean) => {
      release()
      // 动画期间卸掉裁剪/投影，真机上少一大块光栅化成本
      frame.setAttribute('data-drawer-animating', '')
      if (close) {
        closeMobileSider()
      } else {
        openMobileSider()
      }
      lastToggleAt.current = Date.now()
      frame.style.removeProperty('--drawer-progress')
      window.setTimeout(() => {
        frame.removeAttribute('data-drawer-animating')
        frame.style.removeProperty('will-change')
      }, 280)"""
assert OLD in hook, 'settle block not found'
hook = hook.replace(OLD, NEW, 1)
HOOK.write_text(hook, encoding='utf-8')
print('JS toggles data-drawer-animating')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 47', gradle), encoding='utf-8')
print('versionCode 47')
