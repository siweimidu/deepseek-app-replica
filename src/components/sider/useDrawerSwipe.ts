import { useEffect, useRef } from 'react'
import { create } from 'zustand'
import { android } from '../../app/android.js'
import { closeMobileSider, openMobileSider, useMobileSider } from './mobileSiderState.js'

/**
 * 侧边栏横滑（方向无关版）
 *
 * 行为：聊天页上横滑（左或右）→ 打开侧边栏；侧边栏上横滑（左或右）→ 回到对话。
 * 不再锁定方向 —— 之前按单一方向硬编码，与用户实际手势相反时表现为"完全不动"。
 *
 * 通道（三条，任一存活即可切换）：
 * 1. 原生：MainActivity.dispatchTouchEvent 判定横滑 → window.__dshSwipe('left'|'right')
 * 2. JS touch 监听（passive:false + preventDefault 抢手势）
 * 3. JS pointer 监听
 *
 * 手感：跟手位移，松手按距离/速度决定，320ms 弹簧曲线收尾（技能包 spring-default）。
 */

const SLOP = 6
const RATIO = 1.1
const DISTANCE_PX = 22
const FLICK_VELOCITY = 0.28
const FLICK_WINDOW_MS = 160
const COOLDOWN_MS = 300

const clamp01 = (value: number) => Math.max(0, Math.min(1, value))

type DebugState = { visible: boolean; down: number; move: number; toggle: number; last: string }

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
  axis: false | 'opening' | 'closing'
  progress: number
  lastX: number
  lastAt: number
  velocity: number
}

export const useDrawerSwipe = (frameRef: { current: HTMLElement | null }) => {
  const drag = useRef<Drag | null>(null)
  const lastToggleAt = useRef(0)

  useEffect(() => {
    if (!android) {
      return
    }

    /**
     * 每次都现场取容器。
     * 首启没填 Key 时 App 只渲染 API Key 页，容器还没出现；
     * 导入历史后容器也可能被重建 —— 缓存旧元素会让手势彻底失效。
     */
    const frameOf = () => {
      const cached = frameRef.current
      if (cached && cached.isConnected) {
        return cached
      }
      // ref 还没建立、或旧元素已被替换：直接从 DOM 找当前那个
      return (
        (document.querySelector('[data-android-drawer]')?.parentElement as HTMLElement | null) ??
        null
      )
    }

    const drawerWidth = () => {
      const drawer = frameOf()?.querySelector<HTMLElement>('[data-android-drawer]')
      return drawer?.offsetWidth || window.innerWidth
    }

    const claim = () => {
      const frame = frameOf()
      if (!frame) {
        return
      }
      frame.setAttribute('data-drawer-dragging', '')
      frame.style.setProperty('will-change', 'transform')
    }

    const release = () => {
      frameOf()?.removeAttribute('data-drawer-dragging')
    }

    const paint = (progress: number) => {
      frameOf()?.style.setProperty('--drawer-progress', String(clamp01(progress)))
    }

    const settle = (close: boolean) => {
      const frame = frameOf()
      if (!frame) {
        return
      }
      release()
      // 动画期间卸掉裁剪/投影，真机上少一大块光栅化成本
      frame.setAttribute('data-drawer-animating', '')
      if (close) {
        closeMobileSider()
      } else {
        openMobileSider()
      }
      lastToggleAt.current = Date.now()
      frame.style.removeProperty('--drawer-progress')
      window.setTimeout(() => {
        frame.removeAttribute('data-drawer-animating')
        frame.style.removeProperty('will-change')
      }, 280)
      useSwipeDebug.setState((state) => ({
        toggle: state.toggle + 1,
        last: `${close ? 'close' : 'open'} @${Date.now() % 1000}`,
      }))
    }

    const begin = (x: number, y: number) => {
      const opened = useMobileSider.getState().open
      drag.current = {
        x,
        y,
        width: drawerWidth(),
        opened,
        axis: false,
        progress: opened ? 1 : 0,
        lastX: x,
        lastAt: performance.now(),
        velocity: 0,
      }
      useSwipeDebug.setState((state) => ({ down: state.down + 1, last: 'down' }))
    }

    /** 返回 true = 已接管，调用方应阻止默认滚动 */
    const move = (x: number, y: number) => {
      const state = drag.current
      if (!state) {
        return false
      }
      const dx = x - state.x
      const dy = y - state.y

      if (!state.axis) {
        if (Math.abs(dx) < SLOP && Math.abs(dy) < SLOP) {
          return false
        }
        if (Math.abs(dx) <= Math.abs(dy) * RATIO) {
          drag.current = null
          useSwipeDebug.setState({ last: 'vertical → 放行' })
          return false
        }
        // 方向无关：横向确立即接管，往当前状态的反向走
        state.axis = state.opened ? 'closing' : 'opening'
        claim()
      }

      const now = performance.now()
      if (now > state.lastAt) {
        state.velocity = (x - state.lastX) / (now - state.lastAt)
      }
      state.lastX = x
      state.lastAt = now
      state.progress =
        state.axis === 'opening' ? Math.abs(dx) / state.width : 1 - Math.abs(dx) / state.width
      paint(state.progress)
      useSwipeDebug.setState((debug) => ({
        move: debug.move + 1,
        last: `${state.axis === 'opening' ? '开' : '关'} ${Math.round(state.progress * 100)}%`,
      }))
      return true
    }

    const decide = (x: number) => {
      const state = drag.current
      drag.current = null
      if (!state || !state.axis) {
        return
      }
      if (Date.now() - lastToggleAt.current < COOLDOWN_MS) {
        release()
        frameOf()?.style.removeProperty('--drawer-progress')
        return
      }
      const dx = x - state.x
      const flick =
        performance.now() - state.lastAt < FLICK_WINDOW_MS &&
        Math.abs(state.velocity) > FLICK_VELOCITY
      // 往反方向切换；不足阈值则回到原状态
      const toggle = flick || Math.abs(dx) >= DISTANCE_PX
      // settle(close)：关闭时(!opened)要开 ⇒ settle(false)；打开时要关 ⇒ settle(true)
      settle(toggle ? state.opened : !state.opened)
    }

    const restore = () => {
      const state = drag.current
      drag.current = null
      if (!state || !state.axis) {
        return
      }
      release()
      frameOf()?.style.removeProperty('--drawer-progress')
      useSwipeDebug.setState({ last: 'cancel → 还原' })
    }

    // ---- 通道 1：原生派发（MainActivity 判定横滑后调用，方向无关）----
    const nativeBridge = (direction: string) => {
      if (Date.now() - lastToggleAt.current < COOLDOWN_MS) {
        return
      }
      const opened = useMobileSider.getState().open
      settle(opened)
      useSwipeDebug.setState({ last: `native ${direction}` })
    }
    ;(window as unknown as Record<string, unknown>).__dshSwipe = nativeBridge

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
      if (move(touch.clientX, touch.clientY) && event.cancelable) {
        event.preventDefault()
      }
    }

    const onTouchEnd = (event: TouchEvent) => {
      const touch = event.changedTouches[0]
      if (touch) {
        decide(touch.clientX)
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
      if (event.pointerType === 'mouse') {
        return
      }
      if (move(event.clientX, event.clientY)) {
        try {
          const frame = frameOf()
          if (frame && !frame.hasPointerCapture(event.pointerId)) {
            frame.setPointerCapture(event.pointerId)
          }
        } catch {
          // 合成事件或指针已失效
        }
      }
    }
    const onPointerUp = (event: PointerEvent) => {
      if (event.pointerType !== 'mouse') {
        decide(event.clientX)
      }
    }

    // 挂在 document 上：容器还没渲染或后来被重建都不影响手势
    document.addEventListener('touchstart', onTouchStart, { passive: true })
    document.addEventListener('touchmove', onTouchMove, { passive: false })
    document.addEventListener('touchend', onTouchEnd, { passive: true })
    document.addEventListener('touchcancel', restore, { passive: true })
    document.addEventListener('pointerdown', onPointerDown, { passive: true })
    document.addEventListener('pointermove', onPointerMove, { passive: true })
    document.addEventListener('pointerup', onPointerUp, { passive: true })
    document.addEventListener('pointercancel', restore, { passive: true })

    return () => {
      delete (window as unknown as Record<string, unknown>).__dshSwipe
      document.removeEventListener('touchstart', onTouchStart)
      document.removeEventListener('touchmove', onTouchMove)
      document.removeEventListener('touchend', onTouchEnd)
      document.removeEventListener('touchcancel', restore)
      document.removeEventListener('pointerdown', onPointerDown)
      document.removeEventListener('pointermove', onPointerMove)
      document.removeEventListener('pointerup', onPointerUp)
      document.removeEventListener('pointercancel', restore)
      release()
      frameOf()?.style.removeProperty('--drawer-progress')
      frameOf()?.style.removeProperty('will-change')
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
