"""引入 motion 的真实弹簧驱动抽屉与卡片；按官方校准收起按钮。"""

import re
from pathlib import Path

# ---------- 1) 弹簧模块 ----------
SPRING = Path('src/app/spring.ts')
SPRING.write_text("""import { animate, type AnimationPlaybackControls } from 'motion'

/**
 * 弹簧参数（参考 motion / framer-motion 的物理模型）
 * 刚度越高起手越快，阻尼越高收尾越干脆。
 */
export const DRAWER_SPRING = { type: 'spring', stiffness: 560, damping: 42, mass: 0.9 } as const
export const CARD_SPRING = { type: 'spring', stiffness: 400, damping: 38, mass: 0.9 } as const

type Options = {
  velocity?: number
  onUpdate: (value: number) => void
  onComplete?: () => void
}

/** 把一个数值从 from 弹到 to；返回控制句柄，可随时 stop() */
export const springTo = (
  from: number,
  to: number,
  config: typeof DRAWER_SPRING | typeof CARD_SPRING,
  options: Options
): AnimationPlaybackControls =>
  animate(from, to, {
    ...config,
    velocity: options.velocity ?? 0,
    onUpdate: options.onUpdate,
    onComplete: options.onComplete,
  })
""", encoding='utf-8')
print('spring module created')

# ---------- 2) useDrawerSwipe：用弹簧收尾 ----------
HOOK = Path('src/components/sider/useDrawerSwipe.ts')
hook = HOOK.read_text(encoding='utf-8')

hook = hook.replace(
    "import { create } from 'zustand'",
    "import { create } from 'zustand'\nimport { CARD_SPRING, DRAWER_SPRING, springTo } from '../../app/spring.js'",
    1,
)

# 动画句柄
hook = hook.replace(
    "  const lastToggleAt = useRef(0)",
    "  const lastToggleAt = useRef(0)\n  const animations = useRef<{ stop: () => void }[]>([])",
    1,
)

# 跟手时同时写两个变量，卡片和抽屉一起走
hook = hook.replace(
    """    const paint = (progress: number) => {
      frame.style.setProperty('--drawer-progress', String(clamp01(progress)))
    }""",
    """    const paint = (progress: number) => {
      const value = String(clamp01(progress))
      frame.style.setProperty('--drawer-progress', value)
      frame.style.setProperty('--card-progress', value)
    }

    const stopAnimations = () => {
      animations.current.forEach((item) => item.stop())
      animations.current = []
    }""",
    1,
)

# 旧的 settle 换成弹簧版本
start = hook.index('    const settle = (close: boolean) => {')
end = hook.index('    const begin = (x: number, y: number) => {')
NEW_SETTLE = '''    /**
     * 收尾：用 motion 的弹簧把进度弹到终点。
     * 抽屉和卡片各跑一条弹簧（卡片稍软），所以是真实物理回弹，不是近似曲线。
     */
    const settle = (close: boolean) => {
      release()
      stopAnimations()
      frame.setAttribute('data-drawer-animating', '')

      const from = Number.parseFloat(
        frame.style.getPropertyValue('--drawer-progress') || (close ? '1' : '0')
      )
      const target = close ? 0 : 1
      const velocity = lastVelocity.current / Math.max(1, frame.offsetWidth)

      const finish = () => {
        if (close) {
          closeMobileSider()
        } else {
          openMobileSider()
        }
        lastToggleAt.current = Date.now()
        frame.style.removeProperty('--drawer-progress')
        frame.style.removeProperty('--card-progress')
        frame.removeAttribute('data-drawer-animating')
        frame.style.removeProperty('will-change')
        animations.current = []
        useSwipeDebug.setState((state) => ({ toggle: state.toggle + 1, last: close ? 'close' : 'open' }))
      }

      const drawerAnim = springTo(from, target, DRAWER_SPRING, {
        velocity,
        onUpdate: (value) => frame.style.setProperty('--drawer-progress', String(value)),
      })
      const cardAnim = springTo(from, target, CARD_SPRING, {
        velocity: velocity * 0.8,
        onUpdate: (value) => frame.style.setProperty('--card-progress', String(value)),
        onComplete: finish,
      })
      animations.current = [drawerAnim, cardAnim]
    }

'''
hook = hook[:start] + NEW_SETTLE + hook[end:]

# 记录最后一次速度，用于弹簧初速
hook = hook.replace(
    "  const animations = useRef<{ stop: () => void }[]>([])",
    "  const animations = useRef<{ stop: () => void }[]>([])\n  const lastVelocity = useRef(0)",
    1,
)
hook = hook.replace(
    """      state.progress = state.axis === 'opening' ? -dx / state.width : 1 - dx / state.width
      paint(state.progress)""",
    """      state.progress = state.axis === 'opening' ? -dx / state.width : 1 - dx / state.width
      lastVelocity.current = state.velocity * 1000
      paint(state.progress)""",
    1,
)

# 新手势开始前停掉上一次动画
hook = hook.replace(
    "    const begin = (x: number, y: number) => {\n      const opened = useMobileSider.getState().open",
    "    const begin = (x: number, y: number) => {\n      stopAnimations()\n      const opened = useMobileSider.getState().open",
    1,
)

# 取消时立即还原（不走弹簧）
hook = hook.replace(
    """    const restore = () => {
      const state = drag.current
      drag.current = null
      if (!state || !state.axis) {
        return
      }
      release()""",
    """    const restore = () => {
      stopAnimations()
      const state = drag.current
      drag.current = null
      if (!state || !state.axis) {
        return
      }
      release()""",
    1,
)
hook = hook.replace(
    """      release()
      frame.style.removeProperty('--drawer-progress')
      useSwipeDebug.setState({ last: 'cancel → 还原' })""",
    """      release()
      frame.style.removeProperty('--drawer-progress')
      frame.style.removeProperty('--card-progress')
      frame.removeAttribute('data-drawer-animating')
      useSwipeDebug.setState({ last: 'cancel → 还原' })""",
    1,
)

# 不变量：动画期间不要覆盖进度
hook = hook.replace(
    "        if (!frame || frame.hasAttribute('data-drawer-dragging')) {",
    "        if (!frame || frame.hasAttribute('data-drawer-dragging') || frame.hasAttribute('data-drawer-animating')) {",
    1,
)
HOOK.write_text(hook, encoding='utf-8')
print('spring settle wired')

# ---------- 3) CSS：卡片读 --card-progress；动画期间禁用过渡 ----------
APP = Path('src/app/App.module.css')
app = APP.read_text(encoding='utf-8')
app = app.replace(
    'transform: translateX(calc(var(--drawer-width, var(--drawer-edge)) * var(--drawer-progress)));',
    'transform: translateX(calc(var(--drawer-width, var(--drawer-edge)) * var(--card-progress, var(--drawer-progress))));',
)
if '--card-progress' not in app:
    app += """
/* 弹簧动画期间交给 JS 逐帧写变量，CSS 过渡必须关掉 */
[data-android] .frame[data-drawer-animating] {
  --drawer-transition: 0ms;
  --card-transition: 0ms;
}
"""
    APP.write_text(app, encoding='utf-8')
    print('css card-progress + no-transition wired')

# ---------- 4) 收起按钮按官方校准（更大、间距更明显） ----------
SIDER_CSS = Path('src/components/sider/Sider.module.css')
css = SIDER_CSS.read_text(encoding='utf-8')
css = css.replace(
    """[data-android] .collapse {
  display: grid;
  flex-shrink: 0;
  width: 34px;
  height: 34px;""",
    """[data-android] .collapse {
  display: grid;
  flex-shrink: 0;
  width: 40px;
  height: 40px;""",
)
css = css.replace(
    """[data-android] .searchRow {
  display: flex;
  align-items: center;
  gap: 10px;
}""",
    """[data-android] .searchRow {
  display: flex;
  align-items: center;
  gap: 14px;
}""",
)
SIDER_CSS.write_text(css, encoding='utf-8')

ICONS = Path('src/components/base/appIcons.tsx')
icons = ICONS.read_text(encoding='utf-8')
icons = icons.replace(
    """export const IconCollapseSidebar16 = () => (
  <svg
    width="20"
    height="20\"""",
    """export const IconCollapseSidebar16 = () => (
  <svg
    width="22"
    height="22\"""",
)
ICONS.write_text(icons, encoding='utf-8')
print('collapse button sized to official')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 54', gradle), encoding='utf-8')
print('versionCode 54')
