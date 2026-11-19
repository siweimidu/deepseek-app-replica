"""修复：手势绑定在旧元素上导致填 Key / 导入后横滑失效。
改为监听 document，元素每次现场解析。
"""

from pathlib import Path

HOOK = Path('src/components/sider/useDrawerSwipe.ts')
src = HOOK.read_text(encoding='utf-8')

# 1) 不再缓存元素，改成现场解析
src = src.replace(
    """    const frame = frameRef.current
    if (!frame || !android) {
      return
    }
""",
    """    if (!android) {
      return
    }

    /**
     * 每次都现场取容器。
     * 首启没填 Key 时 App 只渲染 API Key 页，容器还没出现；
     * 导入历史后容器也可能被重建 —— 缓存旧元素会让手势彻底失效。
     */
    const frameOf = () =>
      frameRef.current ??
      ((document.querySelector('[data-android-drawer]')?.parentElement as HTMLElement | null) ??
        null)
""",
    1,
)

# 2) 各辅助函数内部自己取元素
src = src.replace(
    """    const drawerWidth = () => {
      const drawer = frame.querySelector<HTMLElement>('[data-android-drawer]')
      return drawer?.offsetWidth || window.innerWidth
    }""",
    """    const drawerWidth = () => {
      const drawer = frameOf()?.querySelector<HTMLElement>('[data-android-drawer]')
      return drawer?.offsetWidth || window.innerWidth
    }""",
    1,
)
src = src.replace(
    """    const claim = () => {
      frame.setAttribute('data-drawer-dragging', '')
      frame.style.setProperty('will-change', 'transform')
    }""",
    """    const claim = () => {
      const frame = frameOf()
      if (!frame) {
        return
      }
      frame.setAttribute('data-drawer-dragging', '')
      frame.style.setProperty('will-change', 'transform')
    }""",
    1,
)
src = src.replace(
    """    const release = () => {
      frame.removeAttribute('data-drawer-dragging')
    }""",
    """    const release = () => {
      frameOf()?.removeAttribute('data-drawer-dragging')
    }""",
    1,
)
src = src.replace(
    """    const paint = (progress: number) => {
      frame.style.setProperty('--drawer-progress', String(clamp01(progress)))
    }""",
    """    const paint = (progress: number) => {
      frameOf()?.style.setProperty('--drawer-progress', String(clamp01(progress)))
    }""",
    1,
)
src = src.replace(
    """    const settle = (close: boolean) => {
      release()""",
    """    const settle = (close: boolean) => {
      const frame = frameOf()
      if (!frame) {
        return
      }
      release()""",
    1,
)
# restore 与 cooldown 分支里的 frame
src = src.replace(
    """      if (Date.now() - lastToggleAt.current < COOLDOWN_MS) {
        release()
        frame.style.removeProperty('--drawer-progress')
        return
      }""",
    """      if (Date.now() - lastToggleAt.current < COOLDOWN_MS) {
        release()
        frameOf()?.style.removeProperty('--drawer-progress')
        return
      }""",
    1,
)
src = src.replace(
    """      release()
      frame.style.removeProperty('--drawer-progress')
      useSwipeDebug.setState({ last: 'cancel → 还原' })""",
    """      release()
      frameOf()?.style.removeProperty('--drawer-progress')
      useSwipeDebug.setState({ last: 'cancel → 还原' })""",
    1,
)

# 3) 指针捕获也现场取
src = src.replace(
    """        try {
          if (!frame.hasPointerCapture(event.pointerId)) {
            frame.setPointerCapture(event.pointerId)
          }
        } catch {""",
    """        try {
          const frame = frameOf()
          if (frame && !frame.hasPointerCapture(event.pointerId)) {
            frame.setPointerCapture(event.pointerId)
          }
        } catch {""",
    1,
)

# 4) 监听挂到 document（元素出现前也有效）
src = src.replace(
    """    frame.addEventListener('touchstart', onTouchStart, { passive: true })
    frame.addEventListener('touchmove', onTouchMove, { passive: false })
    frame.addEventListener('touchend', onTouchEnd, { passive: true })
    frame.addEventListener('touchcancel', restore, { passive: true })
    frame.addEventListener('pointerdown', onPointerDown, { passive: true })
    frame.addEventListener('pointermove', onPointerMove, { passive: true })
    frame.addEventListener('pointerup', onPointerUp, { passive: true })
    frame.addEventListener('pointercancel', restore, { passive: true })""",
    """    // 挂在 document 上：容器还没渲染或后来被重建都不影响手势
    document.addEventListener('touchstart', onTouchStart, { passive: true })
    document.addEventListener('touchmove', onTouchMove, { passive: false })
    document.addEventListener('touchend', onTouchEnd, { passive: true })
    document.addEventListener('touchcancel', restore, { passive: true })
    document.addEventListener('pointerdown', onPointerDown, { passive: true })
    document.addEventListener('pointermove', onPointerMove, { passive: true })
    document.addEventListener('pointerup', onPointerUp, { passive: true })
    document.addEventListener('pointercancel', restore, { passive: true })""",
    1,
)
src = src.replace(
    """      frame.removeEventListener('touchstart', onTouchStart)
      frame.removeEventListener('touchmove', onTouchMove)
      frame.removeEventListener('touchend', onTouchEnd)
      frame.removeEventListener('touchcancel', restore)
      frame.removeEventListener('pointerdown', onPointerDown)
      frame.removeEventListener('pointermove', onPointerMove)
      frame.removeEventListener('pointerup', onPointerUp)
      frame.removeEventListener('pointercancel', restore)""",
    """      document.removeEventListener('touchstart', onTouchStart)
      document.removeEventListener('touchmove', onTouchMove)
      document.removeEventListener('touchend', onTouchEnd)
      document.removeEventListener('touchcancel', restore)
      document.removeEventListener('pointerdown', onPointerDown)
      document.removeEventListener('pointermove', onPointerMove)
      document.removeEventListener('pointerup', onPointerUp)
      document.removeEventListener('pointercancel', restore)""",
    1,
)
src = src.replace(
    """      frame.style.removeProperty('--drawer-progress')
      frame.style.removeProperty('will-change')""",
    """      frameOf()?.style.removeProperty('--drawer-progress')
      frameOf()?.style.removeProperty('will-change')""",
    1,
)

# 5) 第二个 effect（不变量同步）也现场取
src = src.replace(
    """      const frame = frameRef.current
      if (!frame || frame.hasAttribute('data-drawer-dragging')) {""",
    """      const frame = frameOf()
      if (!frame || frame.hasAttribute('data-drawer-dragging')) {""",
    1,
)
HOOK.write_text(src, encoding='utf-8')
print('gesture decoupled from element lifetime')
print('frame.addEventListener left:', src.count('frame.addEventListener'))
