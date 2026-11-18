import { useEffect, useRef } from 'react'
import { flushSync } from 'react-dom'
import { android } from '../../app/android.js'
import { closeMobileSider, openMobileSider, useMobileSider } from './mobileSiderState.js'

/**
 * 侧边栏横滑（整块重写）
 *
 * 规则只有两条：
 *   对话页  —— 只能「向左横滑」拉出侧边栏
 *   侧边栏  —— 只能「向右横滑」回到对话
 *
 * 反方向、竖直方向、输入框上的滑动一律不管，交给页面自己处理。
 *
 * 实现要点：
 * 1. 只监听 touch 事件（WebView 里 pointer 会被合成器取消），绑在 document 上，
 *    不依赖任何元素何时挂载。
 * 2. 拖拽期间写 --drawer-progress 跟手；松手时先同步提交开合状态、再撤内联值，
 *    过渡自然收尾，既不会闪也不会停在半途。
 * 3. 订阅 store：打开 ⇒ 进度恒为 1，关闭 ⇒ 不留内联进度。机制上杜绝"停在半路"。
 */

const SLOP = 8
const RATIO = 1.2
const OPEN_PX = 28
const CLOSE_PX = 28
const OPEN_RATIO = 0.18
const CLOSE_RATIO = 0.82

type Phase = 'idle' | 'pending' | 'opening' | 'closing'

type Gesture = {
  phase: Phase
  startX: number
  startY: number
  width: number
  progress: number
}

export const useDrawerSwipe = (frameRef: { current: HTMLElement | null }) => {
  const gesture = useRef<Gesture | null>(null)

  useEffect(() => {
    if (!android) {
      return
    }

    const frame = () => frameRef.current
    const drawerWidth = () => {
      const node = frame()?.querySelector<HTMLElement>('[data-android-drawer]')
      return node?.offsetWidth || window.innerWidth
    }

    /** 用内联进度跟手 */
    const paint = (progress: number) => {
      const node = frame()
      if (!node) {
        return
      }
      node.setAttribute('data-drawer-dragging', '')
      node.style.setProperty('--drawer-progress', String(Math.max(0, Math.min(1, progress))))
    }

    /** 收尾：先提交状态，再撤内联值，让过渡从当前位置动画到终点 */
    const settle = (open: boolean) => {
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
    }

    const onStart = (event: TouchEvent) => {
      if (event.touches.length !== 1) {
        gesture.current = null
        return
      }
      const touch = event.touches[0]
      if (
        event.target instanceof Element &&
        event.target.closest('input, textarea, [data-drawer-gesture-ignore]')
      ) {
        gesture.current = null
        return
      }
      gesture.current = {
        phase: 'pending',
        startX: touch.clientX,
        startY: touch.clientY,
        width: drawerWidth(),
        progress: useMobileSider.getState().open ? 1 : 0,
      }
    }

    const onMove = (event: TouchEvent) => {
      const state = gesture.current
      const touch = event.touches[0]
      if (!state || !touch || event.touches.length !== 1) {
        return
      }
      const dx = touch.clientX - state.startX
      const dy = touch.clientY - state.startY
      const opened = useMobileSider.getState().open

      if (state.phase === 'pending') {
        if (Math.abs(dx) < SLOP && Math.abs(dy) < SLOP) {
          return
        }
        // 横向必须明显大于纵向，否则交还给滚动
        if (Math.abs(dx) <= Math.abs(dy) * RATIO) {
          gesture.current = null
          return
        }
        // 方向是硬规则：关闭时只认向左，打开时只认向右
        if (!opened && dx < 0) {
          state.phase = 'opening'
        } else if (opened && dx > 0) {
          state.phase = 'closing'
        } else {
          gesture.current = null
          return
        }
      }

      if (state.phase === 'opening') {
        state.progress = -dx / state.width
      } else if (state.phase === 'closing') {
        state.progress = 1 - dx / state.width
      } else {
        return
      }
      paint(state.progress)
    }

    const onEnd = () => {
      const state = gesture.current
      gesture.current = null
      if (!state) {
        return
      }
      if (state.phase === 'opening') {
        const travelled = state.progress * state.width
        settle(travelled >= OPEN_PX || state.progress > OPEN_RATIO)
      } else if (state.phase === 'closing') {
        const travelled = (1 - state.progress) * state.width
        settle(!(travelled >= CLOSE_PX || state.progress < CLOSE_RATIO))
      }
    }

    const onCancel = () => {
      const state = gesture.current
      gesture.current = null
      if (!state || state.phase === 'pending') {
        return
      }
      // 取消时回到拖动前的状态
      settle(useMobileSider.getState().open)
    }

    document.addEventListener('touchstart', onStart, { passive: true })
    document.addEventListener('touchmove', onMove, { passive: true })
    document.addEventListener('touchend', onEnd, { passive: true })
    document.addEventListener('touchcancel', onCancel, { passive: true })

    return () => {
      document.removeEventListener('touchstart', onStart)
      document.removeEventListener('touchmove', onMove)
      document.removeEventListener('touchend', onEnd)
      document.removeEventListener('touchcancel', onCancel)
      const node = frame()
      node?.removeAttribute('data-drawer-dragging')
      node?.style.removeProperty('--drawer-progress')
    }
  }, [frameRef])

  // 不变量：打开 ⇒ 进度 1；关闭 ⇒ 无内联进度（拖拽中不干预）
  useEffect(
    () =>
      useMobileSider.subscribe((state) => {
        const node = frameRef.current
        if (!node || node.hasAttribute('data-drawer-dragging')) {
          return
        }
        if (state.open) {
          node.style.setProperty('--drawer-progress', '1')
        } else {
          node.style.removeProperty('--drawer-progress')
        }
      }),
    [frameRef],
  )
}
