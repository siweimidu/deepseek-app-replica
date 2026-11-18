"""Make the drawer drag drive --drawer-progress so the card moves together."""

from pathlib import Path

SIDER = Path('src/components/sider/Sider.tsx')
text = SIDER.read_text(encoding='utf-8')

OLD_HELPERS = """  /** 手势进行中直接改位移，松手再交给过渡动画收尾 */
  const setOffset = (offset: number) => {
    const element = drawer.current
    if (!element) {
      return
    }
    element.style.setProperty('--drawer-drag', `${offset}px`)
  }

  const settle = (close: boolean) => {
    const element = drawer.current
    if (!element) {
      return
    }
    const width = element.getBoundingClientRect().width
    element.style.transition = ''
    if (!close) {
      setOffset(0)
      return
    }
    // 先滑到底，动画结束后再真正关闭，避免自定义属性不参与过渡造成的跳变
    setOffset(-width)
    window.setTimeout(() => {
      closeMobileSider()
      requestAnimationFrame(() => setOffset(0))
    }, 260)
  }
"""
NEW_HELPERS = """  /** 拖动与卡片共用 --drawer-progress：改一个值两边一起动，不会一个动一个不动 */
  const setProgress = (value: number) => {
    const frame = drawer.current?.parentElement
    if (!frame) {
      return
    }
    frame.style.setProperty('--drawer-progress', String(Math.min(1, Math.max(0, value))))
  }

  const releaseDrag = () => {
    const frame = drawer.current?.parentElement
    if (!frame) {
      return
    }
    frame.removeAttribute('data-drawer-dragging')
    frame.style.removeProperty('--drawer-progress')
  }

  const settle = (close: boolean) => {
    releaseDrag()
    const width = drawer.current?.getBoundingClientRect().width ?? 0
    if (close && width > 0) {
      // 让状态驱动的过渡从当前位置继续滑出，而不是跳变
      closeMobileSider()
      return
    }
    if (!close) {
      // 松手位置已过阈值就回到完全打开
      setProgress(1)
      requestAnimationFrame(() => releaseDrag())
    }
  }
"""
assert OLD_HELPERS in text, 'helpers not found'
text = text.replace(OLD_HELPERS, NEW_HELPERS, 1)

OLD_MOVE = """            state.horizontal = true
            dragged.current = true
            try {
              element.setPointerCapture(event.pointerId)
            } catch {
              // 指针已失效（例如被系统收回）时忽略即可
            }
            element.style.transition = 'none'
          }
          setOffset(Math.min(0, Math.max(-state.width, dx)))"""
NEW_MOVE = """            state.horizontal = true
            dragged.current = true
            try {
              element.setPointerCapture(event.pointerId)
            } catch {
              // 指针已失效（例如被系统收回）时忽略即可
            }
            element.parentElement?.setAttribute('data-drawer-dragging', '')
          }
          setProgress(1 + Math.min(0, Math.max(-state.width, dx)) / state.width)"""
assert OLD_MOVE in text, 'move handler not found'
text = text.replace(OLD_MOVE, NEW_MOVE, 1)

OLD_UP = """          const offset = Number.parseFloat(element?.style.getPropertyValue('--drawer-drag') ?? '0') || 0
          settle(offset < -state.width * 0.24)"""
NEW_UP = """          const progress =
            Number.parseFloat(
              element?.parentElement?.style.getPropertyValue('--drawer-progress') ?? '1'
            ) || 1
          settle(progress < 0.76)"""
assert OLD_UP in text, 'up handler not found'
text = text.replace(OLD_UP, NEW_UP, 1)

SIDER.write_text(text, encoding='utf-8')
print('drag now drives --drawer-progress')
