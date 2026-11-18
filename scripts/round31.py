"""Never leave the drawer stuck mid-progress: React owns the attribute, touch events guarantee a close."""

import re
from pathlib import Path

# ---------- 1) 手势结束时不要自己写 dataset，交给 React 管；并清掉残留进度 ----------
HOOK = Path('src/components/sider/useAndroidDrawerGesture.ts')
hook = HOOK.read_text(encoding='utf-8')
OLD = """    frame.dataset.drawerOpen = String(open)
    delete frame.dataset.drawerDragging
    // Let the transition start at the last rendered drag position.
    frame.getBoundingClientRect()
    frame.style.removeProperty('--drawer-progress')
    event.preventDefault()"""
NEW = """    // 属性归 React 管，这里不再直接写，避免 CSS 状态和 store 不一致导致卡在半途
    delete frame.dataset.drawerDragging
    frame.style.removeProperty('--drawer-progress')
    frame.getBoundingClientRect()
    event.preventDefault()"""
assert OLD in hook, 'settle write not found'
hook = hook.replace(OLD, NEW, 1)
HOOK.write_text(hook, encoding='utf-8')
print('settle no longer writes dataset')

# ---------- 2) 抽屉上加触摸兜底：横向左移 22px 立即关闭 ----------
SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')

old_refs = "  const closeSwipe = useRef<{ x: number; y: number; armed: boolean } | null>(null)"
new_refs = """  const closeSwipe = useRef<{ x: number; y: number; armed: boolean } | null>(null)
  const touchSwipe = useRef<{ x: number; y: number } | null>(null)"""
if 'touchSwipe' not in sider:
    sider = sider.replace(old_refs, new_refs, 1)

    # 触摸事件兜底（pointer 被合成器取消时仍可用）
    old_attrs = """        onPointerDown={(event) => {
          if (!android || !open) {
            return
          }
          closeSwipe.current = { x: event.clientX, y: event.clientY, armed: true }"""
    new_attrs = """        onTouchStart={(event) => {
          const touch = event.touches[0]
          if (!android || !open || !touch) {
            return
          }
          touchSwipe.current = { x: touch.clientX, y: touch.clientY }
        }}
        onTouchMove={(event) => {
          const state = touchSwipe.current
          const touch = event.touches[0]
          if (!state || !touch || !open) {
            return
          }
          const dx = touch.clientX - state.x
          const dy = touch.clientY - state.y
          if (dx < -22 && Math.abs(dx) > Math.abs(dy) * 1.2) {
            touchSwipe.current = null
            closeSwipe.current = null
            drag.current = null
            drawer.current?.parentElement?.removeAttribute('data-drawer-dragging')
            drawer.current?.parentElement?.style.removeProperty('--drawer-progress')
            closeMobileSider()
          }
        }}
        onTouchEnd={() => {
          touchSwipe.current = null
        }}
        onTouchCancel={() => {
          touchSwipe.current = null
        }}
        onPointerDown={(event) => {
          if (!android || !open) {
            return
          }
          closeSwipe.current = { x: event.clientX, y: event.clientY, armed: true }"""
    assert old_attrs in sider, 'pointerdown anchor not found'
    sider = sider.replace(old_attrs, new_attrs, 1)
    SIDER.write_text(sider, encoding='utf-8')
    print('touch close fallback added')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 31', gradle), encoding='utf-8')
print('versionCode 31')
