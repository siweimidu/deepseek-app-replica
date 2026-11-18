"""Guarantee a close path for the drawer, and align the three header glyphs' bottoms."""

import re
from pathlib import Path

# ---------- 1) 抽屉关闭不再只依赖 frame 手势 ----------
SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')

old_refs = "  const drag = useRef<{ x: number; y: number; width: number; horizontal: boolean } | null>(null)\n  const dragged = useRef(false)"
new_refs = """  const drag = useRef<{ x: number; y: number; width: number; horizontal: boolean } | null>(null)
  const dragged = useRef(false)
  // 兜底：不依赖 frame 手势（键盘属性等会整体禁用它），只要往左带过就关闭
  const closeSwipe = useRef<{ x: number; y: number; armed: boolean } | null>(null)"""
assert old_refs in sider
if 'closeSwipe' not in sider:
    sider = sider.replace(old_refs, new_refs, 1)

    old_down = """        onPointerDown={(event) => {
          if (!android || !open) {
            return
          }
          // 每次按下都复位：上一次拖拽若被系统打断，标志会一直为真，导致后续点击全被吞掉
          dragged.current = false"""
    new_down = """        onPointerDown={(event) => {
          if (!android || !open) {
            return
          }
          closeSwipe.current = { x: event.clientX, y: event.clientY, armed: true }
          // 每次按下都复位：上一次拖拽若被系统打断，标志会一直为真，导致后续点击全被吞掉
          dragged.current = false"""
    assert old_down in sider, 'pointerdown not found'
    sider = sider.replace(old_down, new_down, 1)

    old_up = """        onPointerUp={(event) => {
          const state = drag.current"""
    new_up = """        onPointerUp={(event) => {
          const swipe = closeSwipe.current
          closeSwipe.current = null
          if (swipe?.armed) {
            const dx = event.clientX - swipe.x
            const dy = event.clientY - swipe.y
            // 往左 20px 且横向为主：直接收起，不依赖进度与手势模块
            if (dx < -20 && Math.abs(dx) > Math.abs(dy)) {
              closeMobileSider()
              drag.current = null
              return
            }
          }
          const state = drag.current"""
    assert old_up in sider, 'pointerup not found'
    sider = sider.replace(old_up, new_up, 1)

    old_cancel = """        onPointerCancel={() => {
          if (drag.current?.horizontal) {
            settle(false)
          }
          drag.current = null
          dragged.current = false
        }}"""
    new_cancel = """        onPointerCancel={() => {
          if (drag.current?.horizontal) {
            settle(false)
          }
          drag.current = null
          dragged.current = false
          closeSwipe.current = null
        }}"""
    if old_cancel in sider:
        sider = sider.replace(old_cancel, new_cancel, 1)

    SIDER.write_text(sider, encoding='utf-8')
    print('drawer close fallback added')

# 键盘打开时也允许"关闭抽屉"这个方向
HOOK = Path('src/components/sider/useAndroidDrawerGesture.ts')
hook = HOOK.read_text(encoding='utf-8')
hook = hook.replace(
    "      document.documentElement.hasAttribute('data-keyboard') ||",
    "      (document.documentElement.hasAttribute('data-keyboard') &&\n        !useMobileSider.getState().open) ||",
)
HOOK.write_text(hook, encoding='utf-8')
print('keyboard guard only blocks opening')

# ---------- 2) 三个图标的底部对齐 ----------
HEADER = Path('src/components/session/MobileHeader.module.css')
header = HEADER.read_text(encoding='utf-8')
if 'translateY(0.6px)' not in header:
    header += """
/* 三个图标按字形底部对齐（听筒字形本身偏高） */
[data-android] .call svg {
  transform: translateY(0.7px);
}

[data-android] .sound svg,
[data-android] .newChat svg {
  transform: translateY(0);
}
"""
    HEADER.write_text(header, encoding='utf-8')
    print('header glyph bottoms aligned')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 30', gradle), encoding='utf-8')
print('versionCode 30')
