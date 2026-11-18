"""Make the open/close commit order deterministic: state first (sync), inline cleanup after."""

from pathlib import Path

HOOK = Path('src/components/sider/useDrawerSwipe.ts')
hook = HOOK.read_text(encoding='utf-8')

hook = hook.replace(
    "import { useEffect, useRef } from 'react'",
    "import { useEffect, useRef } from 'react'\nimport { flushSync } from 'react-dom'",
    1,
)

OLD = """      window.clearTimeout(state.timer)
      state.timer = window.setTimeout(() => {
        if (close) {
          closeMobileSider()
        } else {
          openMobileSider()
        }
        clearInline()
        track.current = null
      }, 200)"""
NEW = """      window.clearTimeout(state.timer)
      state.timer = window.setTimeout(() => {
        // 先把状态真正提交到 DOM（data-drawer-open），再清内联变量：
        // 顺序反了的话 DOM 还停在旧状态，清完内联值会让抽屉先弹回去再打开，看着就是"打不开"
        flushSync(() => {
          if (close) {
            closeMobileSider()
          } else {
            openMobileSider()
          }
        })
        clearInline()
        track.current = null
      }, 200)"""
assert OLD in hook, 'settle timeout not found'
hook = hook.replace(OLD, NEW, 1)
HOOK.write_text(hook, encoding='utf-8')
print('flushSync ordering applied')

# 打开时宽度要提前量好：关闭状态下 --drawer-width 还没写，会导致进度分母不准
SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')
old = """  useEffect(() => {
    const frame = drawer.current?.parentElement
    // 自愈：状态一变就把拖动残留清掉，避免抽屉卡在半途
    frame?.style.removeProperty('--drawer-progress')
    frame?.removeAttribute('data-drawer-dragging')"""
new = """  useEffect(() => {
    const frame = drawer.current?.parentElement
    // 自愈：状态一变就把拖动残留清掉，避免抽屉卡在半途
    frame?.style.removeProperty('--drawer-progress')
    frame?.removeAttribute('data-drawer-dragging')
    // 抽屉一挂载就把宽度记下来，拖动时进度分母才是准的
    syncWidth()"""
if old in sider and '抽屉一挂载就把宽度记下来' not in sider:
    sider = sider.replace(old, new, 1)
    SIDER.write_text(sider, encoding='utf-8')
    print('drawer width measured on mount')
