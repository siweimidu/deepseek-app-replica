"""Deterministic settle: enable transition, commit state, then drop the inline value."""

from pathlib import Path

HOOK = Path('src/components/sider/useDrawerSwipe.ts')
hook = HOOK.read_text(encoding='utf-8')

start = hook.index("    /** 从当前位置过渡到终点，动画结束后再切状态，再清内联值 */")
end = hook.index("    const onStart = (event: TouchEvent) => {")
NEW = """    /**
     * 松手收尾：启用过渡 → 同步提交开合状态 → 撤掉内联进度。
     * 撤掉内联值的那一瞬，计算值从当前拖动位置变成 CSS 目标值，
     * 过渡会自己把它动画过去，不存在"先弹回再打开"的顺序问题。
     */
    const settle = (close: boolean) => {
      const state = track.current
      if (!state) {
        return
      }
      state.phase = 'settling'
      track.current = null
      const frame = frameOf()
      if (!frame) {
        return
      }
      frame.removeAttribute('data-drawer-dragging')
      flushSync(() => {
        if (close) {
          closeMobileSider()
        } else {
          openMobileSider()
        }
      })
      frame.style.removeProperty('--drawer-progress')
    }

"""
hook = hook[:start] + NEW + hook[end:]

# timer 字段不再需要
hook = hook.replace("  progress: number\n  timer: number\n", "  progress: number\n", 1)
hook = hook.replace("        progress: useMobileSider.getState().open ? 1 : 0,\n        timer: 0,\n", "        progress: useMobileSider.getState().open ? 1 : 0,\n", 1)

HOOK.write_text(hook, encoding='utf-8')
print('deterministic settle applied:', 'window.setTimeout' not in hook)
