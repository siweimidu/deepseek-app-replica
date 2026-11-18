"""Bind drawer swipe on document so mount timing can never disable the gesture."""

from pathlib import Path

HOOK = Path('src/components/sider/useDrawerSwipe.ts')
hook = hook_text = HOOK.read_text(encoding='utf-8')

hook = hook.replace(
    """  useEffect(() => {
    const frame = frameRef.current
    if (!frame || !android) {
      return
    }

    const setProgress = (value: number) => {
      frame.style.setProperty('--drawer-progress', String(Math.max(0, Math.min(1, value))))
    }

    const clearInline = () => {
      frame.removeAttribute('data-drawer-dragging')
      frame.style.removeProperty('--drawer-progress')
    }""",
    """  useEffect(() => {
    if (!android) {
      return
    }

    const frameOf = () => frameRef.current

    const setProgress = (value: number) => {
      frameOf()?.style.setProperty('--drawer-progress', String(Math.max(0, Math.min(1, value))))
    }

    const clearInline = () => {
      const frame = frameOf()
      frame?.removeAttribute('data-drawer-dragging')
      frame?.style.removeProperty('--drawer-progress')
    }""",
)

hook = hook.replace(
    """      const drawer = frame.querySelector<HTMLElement>('[data-android-drawer]')
      if (!drawer) {
        return
      }""",
    """      const frame = frameOf()
      if (!frame) {
        return
      }
      const drawer = frame.querySelector<HTMLElement>('[data-android-drawer]')
      if (!drawer) {
        return
      }""",
)

hook = hook.replace(
    """      state.phase = 'dragging'
      frame.setAttribute('data-drawer-dragging', '')""",
    """      state.phase = 'dragging'
      frameOf()?.setAttribute('data-drawer-dragging', '')""",
)

hook = hook.replace(
    """      state.phase = 'settling'
      const target = close ? 0 : 1
      frame.removeAttribute('data-drawer-dragging')""",
    """      state.phase = 'settling'
      const target = close ? 0 : 1
      frameOf()?.removeAttribute('data-drawer-dragging')""",
)

hook = hook.replace(
    """    frame.addEventListener('touchstart', onStart, { passive: true })
    frame.addEventListener('touchmove', onMove, { passive: true })
    frame.addEventListener('touchend', onEnd, { passive: true })
    frame.addEventListener('touchcancel', onCancel, { passive: true })

    return () => {
      frame.removeEventListener('touchstart', onStart)
      frame.removeEventListener('touchmove', onMove)
      frame.removeEventListener('touchend', onEnd)
      frame.removeEventListener('touchcancel', onCancel)
      clearInline()
    }""",
    """    // 绑在 document 上：不依赖 frame 何时挂载，任何时候都不会失效
    document.addEventListener('touchstart', onStart, { passive: true })
    document.addEventListener('touchmove', onMove, { passive: true })
    document.addEventListener('touchend', onEnd, { passive: true })
    document.addEventListener('touchcancel', onCancel, { passive: true })

    return () => {
      document.removeEventListener('touchstart', onStart)
      document.removeEventListener('touchmove', onMove)
      document.removeEventListener('touchend', onEnd)
      document.removeEventListener('touchcancel', onCancel)
      clearInline()
    }""",
)

# move 里对 frame 的引用也改成惰性
hook = hook.replace("        frame.setAttribute('data-drawer-dragging', '')", "        frameOf()?.setAttribute('data-drawer-dragging', '')")

HOOK.write_text(hook, encoding='utf-8')
print('bound on document:', "document.addEventListener('touchstart'" in hook)
