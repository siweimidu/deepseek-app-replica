"""Header phone chip, edge-swipe to open the drawer, voice card as a gradient preview."""

import re
from pathlib import Path

# ---------- 1) 电话按钮：官方是带圆形底的独立按钮 ----------
HEADER = Path('src/components/session/MobileHeader.module.css')
header = HEADER.read_text(encoding='utf-8')
if '.call' not in header:
    header += """
/* 官方：电话是带圆形底色的按钮，比两侧裸图标更"重"一点 */
[data-android] .call {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--dsw-alias-label-primary) 10%, transparent);
  margin: 0 6px;

  svg {
    width: 24px;
    height: 24px;
  }
}

[data-android] .sound {
  margin: 0 4px;
}
"""
    HEADER.write_text(header, encoding='utf-8')
    print('phone chip styled')

# ---------- 2) 对话页右滑拉出抽屉（与关闭共用同一个 progress 变量） ----------
APP = Path('src/app/App.tsx')
app = APP.read_text(encoding='utf-8')

if 'openMobileSider' not in app:
    app = app.replace(
        "import { useIsMobile, useMobileViewport, usePreventPageScroll } from './viewport.js'",
        "import { useIsMobile, useMobileViewport, usePreventPageScroll } from './viewport.js'\nimport { openMobileSider } from '../components/sider/mobileSiderState.js'",
        1,
    )

if 'swipeRef' not in app:
    app = app.replace(
        "  return (",
        """  // 对话页右滑拉出抽屉：和关闭手势共用 --drawer-progress，抽屉与卡片一起动
  const swipeRef = useRef<{ x: number; y: number; width: number; horizontal: boolean } | null>(null)
  const setDrawerProgress = (value: number) => {
    const frame = mainRef.current?.parentElement
    if (!frame) {
      return
    }
    frame.style.setProperty('--drawer-progress', String(Math.min(1, Math.max(0, value))))
  }
  const mainRef = useRef<HTMLElement>(null)

  return (""",
        1,
    )

    app = app.replace(
        """        <main className={styles.main}>""",
        """        <main
          className={styles.main}
          ref={mainRef}
          onPointerDown={(event) => {
            if (!android || drawerOpen) {
              return
            }
            swipeRef.current = {
              x: event.clientX,
              y: event.clientY,
              width: event.currentTarget.getBoundingClientRect().width,
              horizontal: false,
            }
          }}
          onPointerMove={(event) => {
            const state = swipeRef.current
            if (!state) {
              return
            }
            const dx = event.clientX - state.x
            const dy = event.clientY - state.y
            if (!state.horizontal) {
              if (Math.abs(dx) < 6 && Math.abs(dy) < 6) {
                return
              }
              // 只认从右往左？这里是往右滑出抽屉，左滑忽略，纵向交给滚动
              if (dx <= 0 || Math.abs(dx) <= Math.abs(dy) * 1.1) {
                swipeRef.current = null
                return
              }
              state.horizontal = true
              const frame = event.currentTarget.parentElement
              frame?.setAttribute('data-drawer-dragging', '')
            }
            setDrawerProgress(dx / state.width)
          }}
          onPointerUp={(event) => {
            const state = swipeRef.current
            swipeRef.current = null
            if (!state?.horizontal) {
              return
            }
            const frame = event.currentTarget.parentElement
            const dx = event.clientX - state.x
            const opened = dx > state.width * 0.24
            frame?.removeAttribute('data-drawer-dragging')
            frame?.style.removeProperty('--drawer-progress')
            if (opened) {
              openMobileSider()
            }
          }}
          onPointerCancel={() => {
            const frame = mainRef.current?.parentElement
            frame?.removeAttribute('data-drawer-dragging')
            frame?.style.removeProperty('--drawer-progress')
            swipeRef.current = null
          }}
        >""",
        1,
    )
    APP.write_text(app, encoding='utf-8')
    print('edge swipe to open wired')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 25', gradle), encoding='utf-8')
print('versionCode 25')
