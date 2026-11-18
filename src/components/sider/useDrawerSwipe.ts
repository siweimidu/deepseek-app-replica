import { useEffect, useRef } from 'react'
import { create } from 'zustand'
import { android } from '../../app/android.js'
import { closeMobileSider, openMobileSider, useMobileSider } from './mobileSiderState.js'

/**
 * 侧边栏横滑（原生监听版）
 *
 * 规则：对话页向「左」滑 → 打开侧边栏；侧边栏向「右」滑 → 回到对话。
 *
 * 这一版跟前几版的区别，都是为了在真机 WebView 上活下来：
 * 1. **不走 React 合成事件**，直接 addEventListener 到 frame 元素上。
 * 2. **touchmove 用 passive:false**，一旦判定为横滑就 preventDefault()，
 *    等于告诉浏览器"这个手势我接管了"——它就不会再判成滚动、也不会发 touchcancel。
 *    （之前用 passive:true，横滑一开始就被滚动抢走，手势在判向前就死了。）
 * 3. **不依赖 frameRef 之外的东西**：begin 直接用闭包里的元素。
 * 4. 状态切换只调 store，不碰 DOM；跟手只是附加效果。
 * 5. 计数器暴露给调试角标，出问题时能看出断在哪一环。
 */

const SLOP = 7
const RATIO = 1.15
const DISTANCE_PX = 24
const PROGRESS_GATE = 0.18
const COOLDOWN_MS = 320
const FLICK_VELOCITY = 0.3
const FLICK_WINDOW_MS = 140

const clamp01 = (value: number) => Math.max(0, Math.min(1, value))

type DebugState = {
  visible: boolean
  down: number
  move: number
  toggle: number
  last: string
}

export const useSwipeDebug = create<DebugState>(() => ({
  visible: false,
  down: 0,
  move: 0,
  toggle: 0,
  last: '',
}))

export const toggleSwipeDebug = () =>
  useSwipeDebug.setState((state) => ({ visible: !state.visible, last: 'toggled' }))

type Drag = {
  x: number
  y: number
  width: number
  opened: boolean
  decided: false | 'opening' | 'closing'
  progress: number
  lastX: number
  lastAt: number
  velocity: number
}

export const useDrawerSwipe = (frameRef: { current: HTMLElement | null }) => {
  const drag = useRef<Drag | null>(null)
  const lastToggleAt = useRef(0)

  useEffect(() => {
    const frame = frameRef.current
    if (!frame || !android) {
      return
    }

    const drawer = () => frame.querySelector<HTMLElement>('[data-android-drawer]')

    const paint = (progress: number) => {
      frame.setAttribute('data-drawer-dragging', '')
      frame.style.setProperty('--drawer-progress', String(clamp01(progress)))
    }

    const settle = (close: boolean) => {
      frame.removeAttribute('data-drawer-dragging')
      if (close) {
        closeMobileSider()
      } else {
        openMobileSider()
      }
      lastToggleAt.current = Date.now()
      useSwipeDebug.setState((state) => ({
        toggle: state.toggle + 1,
        last: `toggle ${close ? 'close' : 'open'}`,
      }))
      requestAnimationFrame(() => frame.style.removeProperty('--drawer-progress'))
    }

    const begin = (x: number, y: number) => {
      const element = drawer()
      const opened = useMobileSider.getState().open
      drag.current = {
        x,
        y,
        width: element?.offsetWidth || window.innerWidth,
        opened,
        decided: false,
        progress: opened ? 1 : 0,
        lastX: x,
        lastAt: performance.now(),
        velocity: 0,
      }
      useSwipeDebug.setState((state) => ({ down: state.down + 1, last: 'down' }))
    }

    /** 返回 true 表示已接管这次手势 */
    const move = (x: number, y: number) => {
      const state = drag.current
      if (!state) {
        return false
      }
      const dx = x - state.x
      const dy = y - state.y

      if (!state.decided) {
        if (Math.abs(dx) < SLOP && Math.abs(dy) < SLOP) {
          return false
        }
        if (Math.abs(dx) <= Math.abs(dy) * RATIO) {
          drag.current = null
          useSwipeDebug.setState({ last: 'vertical' })
          return false
        }
        if (!state.opened && dx < 0) {
          state.decided = 'opening'
        } else if (state.opened && dx > 0) {
          state.decided = 'closing'
        } else {
          drag.current = null
          useSwipeDebug.setState({ last: 'wrong-direction' })
          return false
        }
      }

      const now = performance.now()
      if (now > state.lastAt) {
        state.velocity = (x - state.lastX) / (now - state.lastAt)
      }
      state.lastX = x
      state.lastAt = now
      state.progress = state.decided === 'opening' ? -dx / state.width : 1 - dx / state.width
      paint(state.progress)
      useSwipeDebug.setState((debug) => ({
        move: debug.move + 1,
        last: `${state.decided} ${Math.round(state.progress * 100)}%`,
      }))
      return true
    }

    const end = (x: number) => {
      const state = drag.current
      drag.current = null
      if (!state || !state.decided) {
        return
      }
      if (Date.now() - lastToggleAt.current < COOLDOWN_MS) {
        frame.removeAttribute('data-drawer-dragging')
        frame.style.removeProperty('--drawer-progress')
        return
      }
      const dx = x - state.x
      const flick =
        performance.now() - state.lastAt < FLICK_WINDOW_MS &&
        Math.abs(state.velocity) > FLICK_VELOCITY
      if (state.decided === 'opening') {
        const open = flick
          ? state.velocity < 0
          : Math.abs(dx) >= DISTANCE_PX || state.progress > PROGRESS_GATE
        settle(!open)
        return
      }
      const close = flick
        ? state.velocity > 0
        : Math.abs(dx) >= DISTANCE_PX || state.progress < 1 - PROGRESS_GATE
      settle(close)
    }

    const cancel = () => {
      const state = drag.current
      drag.current = null
      if (!state || !state.decided) {
        return
      }
      settle(state.progress < 0.5)
    }

    const onTouchStart = (event: TouchEvent) => {
      if (event.touches.length !== 1) {
        return
      }
      const touch = event.touches[0]
      if (
        event.target instanceof Element &&
        event.target.closest('input, textarea, [data-drawer-gesture-ignore]')
      ) {
        return
      }
      begin(touch.clientX, touch.clientY)
    }

    const onTouchMove = (event: TouchEvent) => {
      const touch = event.touches[0]
      if (!touch) {
        return
      }
      // 抢到手就阻止默认行为：浏览器不再判成滚动，也就不会发 touchcancel
      if (move(touch.clientX, touch.clientY) && event.cancelable) {
        event.preventDefault()
      }
    }

    const onTouchEnd = (event: TouchEvent) => {
      const touch = event.changedTouches[0]
      if (touch) {
        end(touch.clientX)
      }
    }

    const onPointerDown = (event: PointerEvent) => {
      if (event.pointerType === 'mouse') {
        return
      }
      if (
        event.target instanceof Element &&
        event.target.closest('input, textarea, [data-drawer-gesture-ignore]')
      ) {
        return
      }
      if (!drag.current) {
        begin(event.clientX, event.clientY)
      }
    }
    const onPointerMove = (event: PointerEvent) => {
      if (event.pointerType !== 'mouse') {
        move(event.clientX, event.clientY)
      }
    }
    const onPointerUp = (event: PointerEvent) => {
      if (event.pointerType !== 'mouse') {
        end(event.clientX)
      }
    }

    frame.addEventListener('touchstart', onTouchStart, { passive: true })
    frame.addEventListener('touchmove', onTouchMove, { passive: false })
    frame.addEventListener('touchend', onTouchEnd, { passive: true })
    frame.addEventListener('touchcancel', cancel, { passive: true })
    frame.addEventListener('pointerdown', onPointerDown, { passive: true })
    frame.addEventListener('pointermove', onPointerMove, { passive: true })
    frame.addEventListener('pointerup', onPointerUp, { passive: true })
    frame.addEventListener('pointercancel', cancel, { passive: true })

    return () => {
      frame.removeEventListener('touchstart', onTouchStart)
      frame.removeEventListener('touchmove', onTouchMove)
      frame.removeEventListener('touchend', onTouchEnd)
      frame.removeEventListener('touchcancel', cancel)
      frame.removeEventListener('pointerdown', onPointerDown)
      frame.removeEventListener('pointermove', onPointerMove)
      frame.removeEventListener('pointerup', onPointerUp)
      frame.removeEventListener('pointercancel', cancel)
      frame.removeAttribute('data-drawer-dragging')
      frame.style.removeProperty('--drawer-progress')
    }
  }, [frameRef])

  // 不变量：打开 ⇒ 进度恒为 1；关闭 ⇒ 不留内联进度（拖拽中不干预）
  useEffect(
    () =>
      useMobileSider.subscribe((state) => {
        const frame = frameRef.current
        if (!frame || frame.hasAttribute('data-drawer-dragging')) {
          return
        }
        if (state.open) {
          frame.style.setProperty('--drawer-progress', '1')
        } else {
          frame.style.removeProperty('--drawer-progress')
        }
      }),
    [frameRef],
  )
}
