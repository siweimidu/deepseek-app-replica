"""Make the swipe independent of the frame ref and stop the browser from cancelling horizontal touches."""

import re
from pathlib import Path

# ---------- 1) frame 上声明 touch-action：横向手势归 JS，纵向归滚动 ----------
APP_CSS = Path('src/app/App.module.css')
css = APP_CSS.read_text(encoding='utf-8')
if 'touch-action: pan-y' not in css:
    css += """
/* 告诉浏览器：纵向滚动归你，横向手势不要取消，交给 JS 处理。
   缺这行时，从可滚动列表上开始的横滑会被判成滚动并触发 touchcancel，表现就是"怎么滑都没反应" */
[data-android] .frame {
  touch-action: pan-y;
}
"""
    APP_CSS.write_text(css, encoding='utf-8')
    print('frame touch-action: pan-y')

# ---------- 2) 不依赖 ref：用时现找，且状态切换与样式解耦 ----------
HOOK = Path('src/components/sider/useDrawerSwipe.ts')
hook = HOOK.read_text(encoding='utf-8')

hook = hook.replace(
    """    const frame = () => frameRef.current""",
    """    /** 用时现找：ref 可能还没挂上，或已被替换，不能只信它 */
    const frame = () =>
      frameRef.current ?? document.querySelector<HTMLElement>('[data-android-drawer]')?.parentElement ?? null""",
    1,
)

OLD_SETTLE = """    const settle = (open: boolean) => {
      const node = frame()
      if (!node) {
        return
      }
      node.removeAttribute('data-drawer-dragging')
      flushSync(() => {
        if (open) {
          openMobileSider()
        } else {
          closeMobileSider()
        }
      })
      node.style.removeProperty('--drawer-progress')
    }"""
NEW_SETTLE = """    const settle = (open: boolean) => {
      // 状态切换永远执行：拿不到节点只是少了样式收尾，不能让开合失效
      const node = frame()
      node?.removeAttribute('data-drawer-dragging')
      flushSync(() => {
        if (open) {
          openMobileSider()
        } else {
          closeMobileSider()
        }
      })
      node?.style.removeProperty('--drawer-progress')
    }"""
assert OLD_SETTLE in hook, 'settle not found'
hook = hook.replace(OLD_SETTLE, NEW_SETTLE, 1)

# ---------- 3) 被 touchcancel 打断时，若方向已经明确就按方向执行 ----------
OLD_CANCEL = """    const onCancel = () => {
      const state = gesture.current
      gesture.current = null
      if (!state || state.phase === 'pending') {
        return
      }
      // 取消时回到拖动前的状态
      settle(useMobileSider.getState().open)
    }"""
NEW_CANCEL = """    const onCancel = () => {
      const state = gesture.current
      gesture.current = null
      if (!state) {
        return
      }
      // 方向已经明确就别听浏览器的：它常把横滑判成滚动而发 touchcancel，
      // 这里按已判定的方向继续执行，保证"滑了就有反应"
      if (state.phase === 'opening') {
        const travelled = state.progress * state.width
        if (travelled >= OPEN_PX || state.progress > OPEN_RATIO) {
          settle(true)
          return
        }
      }
      if (state.phase === 'closing') {
        const travelled = (1 - state.progress) * state.width
        if (travelled >= CLOSE_PX || state.progress < CLOSE_RATIO) {
          settle(false)
          return
        }
      }
      settle(useMobileSider.getState().open)
    }"""
assert OLD_CANCEL in hook, 'cancel not found'
hook = hook.replace(OLD_CANCEL, NEW_CANCEL, 1)

HOOK.write_text(hook, encoding='utf-8')
print('lazy frame + cancel honours direction')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 38', gradle), encoding='utf-8')
print('versionCode 38')
