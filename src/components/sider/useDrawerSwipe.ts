import { useEffect, useRef } from 'react'
import { create } from 'zustand'
import { android } from '../../app/android.js'
import { closeMobileSider, openMobileSider, useMobileSider } from './mobileSiderState.js'

/**
 * 侧边栏横滑
 *
 * 规则：对话页向「左」滑 → 打开侧边栏；侧边栏向「右」滑 → 回到对话。
 *
 * 交互模型按「按下记坑，抬手判定」：
 * - pointerdown：只记录起点，不做任何可见变化（避免"刚按下页面就跳走"）
 * - pointermove：判定方向后才接管手势；接管即 preventDefault（touch, passive:false），
 *   相当于告诉浏览器"这个手势我处理"，它就不会判成滚动、也不会发 touchcancel
 * - pointerup：按距离与速度决定去向；**即时**还原/落位，不等定时器
 * - pointercancel：立刻回到起始状态，绝不停在半途
 *
 * 动画：位移只走 transform（合成器廉价层）；will-change 只在手势与过渡期间挂着。
 * 状态切换只调 store，不依赖任何 DOM 查询——拿不到元素也不会让开合失效。
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
    const frame = frameRef.current
    if (!frame || !android) {
      return
    }

    const drawerWidth = () => {
      const drawer = frame.querySelector<HTMLElement>('[data-android-drawer]')
      return drawer?.offsetWidth || window.innerWidth
    }

    /** 接管手势：挂上临时 will-change，过渡设为 0（跟手） */
    const claim = () => {
      frame.setAttribute('data-drawer-dragging', '')
      frame.style.setProperty('will-change', 'transform')
    }

    const release = () => {
      frame.removeAttribute('data-drawer-dragging')
    }

    const paint = (progress: number) => {
      frame.style.setProperty('--drawer-progress', String(clamp01(progress)))
    }

    /** 即时收尾：先提交状态，同一帧撤掉内联值，交给 CSS 弹簧曲线走完 */
    const settle = (close: boolean) => {
      release()
      if (close) {
        closeMobileSider()
      } else {
        openMobileSider()
      }
      lastToggleAt.current = Date.now()
      // 同一帧内撤内联值：计算值从当前位移变成目标值，过渡立刻从当前位置开始
      frame.style.removeProperty('--drawer-progress')
      window.setTimeout(() => frame.style.removeProperty('will-change'), 420)
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
        if (!state.opened && dx < 0) {
          state.axis = 'opening'
        } else if (state.opened && dx > 0) {
          state.axis = 'closing'
        } else {
          drag.current = null
          useSwipeDebug.setState({ last: '方向不符 → 放行' })
          return false
        }
        claim()
      }

      const now = performance.now()
      if (now > state.lastAt) {
        state.velocity = (x - state.lastX) / (now - state.lastAt)
      }
      state.lastX = x
      state.lastAt = now
      state.progress = state.axis === 'opening' ? -dx / state.width : 1 - dx / state.width
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
        frame.style.removeProperty('--drawer-progress')
        return
      }
      const dx = x - state.x
      const flick =
        performance.now() - state.lastAt < FLICK_WINDOW_MS &&
        Math.abs(state.velocity) > FLICK_VELOCITY
      if (state.axis === 'opening') {
        const open = flick ? state.velocity < 0 : Math.abs(dx) >= DISTANCE_PX
        settle(!open)
        return
      }
      const close = flick ? state.velocity > 0 : Math.abs(dx) >= DISTANCE_PX
      settle(close)
    }

    /** 取消：立刻回到起点，不留半途 */
    const restore = () => {
      const state = drag.current
      drag.current = null
      if (!state || !state.axis) {
        return
      }
      release()
      frame.style.removeProperty('--drawer-progress')
      useSwipeDebug.setState({ last: 'cancel → 还原' })
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
          if (!frame.hasPointerCapture(event.pointerId)) {
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

    frame.addEventListener('touchstart', onTouchStart, { passive: true })
    frame.addEventListener('touchmove', onTouchMove, { passive: false })
    frame.addEventListener('touchend', onTouchEnd, { passive: true })
    frame.addEventListener('touchcancel', restore, { passive: true })
    frame.addEventListener('pointerdown', onPointerDown, { passive: true })
    frame.addEventListener('pointermove', onPointerMove, { passive: true })
    frame.addEventListener('pointerup', onPointerUp, { passive: true })
    frame.addEventListener('pointercancel', restore, { passive: true })

    return () => {
      frame.removeEventListener('touchstart', onTouchStart)
      frame.removeEventListener('touchmove', onTouchMove)
      frame.removeEventListener('touchend', onTouchEnd)
      frame.removeEventListener('touchcancel', restore)
      frame.removeEventListener('pointerdown', onPointerDown)
      frame.removeEventListener('pointermove', onPointerMove)
      frame.removeEventListener('pointerup', onPointerUp)
      frame.removeEventListener('pointercancel', restore)
      release()
      frame.style.removeProperty('--drawer-progress')
      frame.style.removeProperty('will-change')
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
