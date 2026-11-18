import { useCallback, useEffect, useRef, type PointerEvent as ReactPointerEvent, type TouchEvent as ReactTouchEvent } from 'react'
import { android } from '../../app/android.js'
import { closeMobileSider, openMobileSider, useMobileSider } from './mobileSiderState.js'

/**
 * 侧边栏横滑（双通道 + 指针捕获）
 *
 * 规则：对话页向「左」滑打开；侧边栏向「右」滑关闭。
 *
 * 为什么两条通道都要：
 * - pointer：setPointerCapture 后移动事件一定送到，滚动容器抢不走（设备上实测可行）
 * - touch ：pointer 被系统/合成器取消时的兜底
 * 两条通道共用同一个状态机，并用 350ms 冷却去重，避免一次手势被处理两遍。
 */

const SLOP = 7
const RATIO = 1.15
const DISTANCE_PX = 24
const PROGRESS_GATE = 0.18
const FLICK_VELOCITY = 0.3
const FLICK_WINDOW_MS = 140
const COOLDOWN_MS = 350

const clamp01 = (value: number) => Math.max(0, Math.min(1, value))

type Drag = {
  id: number
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

  const paint = useCallback(
    (progress: number) => {
      frameRef.current?.style.setProperty('--drawer-progress', String(clamp01(progress)))
    },
    [frameRef],
  )

  const settle = useCallback(
    (close: boolean) => {
      const frame = frameRef.current
      frame?.removeAttribute('data-drawer-dragging')
      if (close) {
        closeMobileSider()
      } else {
        openMobileSider()
      }
      lastToggleAt.current = Date.now()
      // 下一帧再撤内联值：状态已提交，过渡从当前位移动画到终点
      requestAnimationFrame(() => frameRef.current?.style.removeProperty('--drawer-progress'))
    },
    [frameRef],
  )

  const begin = useCallback(
    (x: number, y: number, id: number) => {
      if (!android) {
        return
      }
      const frame = frameRef.current
      const drawer = frame?.querySelector<HTMLElement>('[data-android-drawer]')
      if (!frame || !drawer) {
        return
      }
      const opened = useMobileSider.getState().open
      drag.current = {
        id,
        x,
        y,
        width: drawer.offsetWidth || window.innerWidth,
        opened,
        decided: false,
        progress: opened ? 1 : 0,
        lastX: x,
        lastAt: performance.now(),
        velocity: 0,
      }
    },
    [frameRef],
  )

  /** 返回 true 表示这次移动被手势接管（调用方可据此阻止滚动） */
  const moveTo = useCallback(
    (x: number, y: number, id: number) => {
      const state = drag.current
      if (!state || state.id !== id) {
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
          return false
        }
        // 方向是硬规则：关闭时只认向左，打开时只认向右
        if (!state.opened && dx < 0) {
          state.decided = 'opening'
        } else if (state.opened && dx > 0) {
          state.decided = 'closing'
        } else {
          drag.current = null
          return false
        }
        frameRef.current?.setAttribute('data-drawer-dragging', '')
      }

      const now = performance.now()
      if (now > state.lastAt) {
        state.velocity = (x - state.lastX) / (now - state.lastAt)
      }
      state.lastX = x
      state.lastAt = now
      state.progress = state.decided === 'opening' ? -dx / state.width : 1 - dx / state.width
      paint(state.progress)
      return true
    },
    [frameRef, paint],
  )

  const end = useCallback(
    (x: number, id: number) => {
      const state = drag.current
      drag.current = null
      if (!state || state.id !== id || !state.decided) {
        return
      }
      if (Date.now() - lastToggleAt.current < COOLDOWN_MS) {
        frameRef.current?.removeAttribute('data-drawer-dragging')
        frameRef.current?.style.removeProperty('--drawer-progress')
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
    },
    [frameRef, settle],
  )

  const cancel = useCallback(
    (id: number) => {
      const state = drag.current
      drag.current = null
      if (!state || state.id !== id || !state.decided) {
        return
      }
      // 被打断时按当前进度落位，绝不留在半途
      settle(state.progress < 0.5)
    },
    [settle],
  )

  // ---- 指针通道 ----
  const onPointerDown = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      if (event.pointerType === 'mouse' || !event.isPrimary) {
        return
      }
      if (
        event.target instanceof Element &&
        event.target.closest('input, textarea, [data-drawer-gesture-ignore]')
      ) {
        return
      }
      begin(event.clientX, event.clientY, event.pointerId)
    },
    [begin],
  )

  const onPointerMove = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      if (!drag.current || drag.current.id !== event.pointerId) {
        return
      }
      const captured = moveTo(event.clientX, event.clientY, event.pointerId)
      if (captured && !event.currentTarget.hasPointerCapture(event.pointerId)) {
        try {
          event.currentTarget.setPointerCapture(event.pointerId)
        } catch {
          // 合成事件 pointerId 无效时忽略
        }
      }
    },
    [moveTo],
  )

  const onPointerUp = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => end(event.clientX, event.pointerId),
    [end],
  )

  const onPointerCancel = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => cancel(event.pointerId),
    [cancel],
  )

  // ---- 触摸通道（兜底）----
  const onTouchStart = useCallback(
    (event: ReactTouchEvent<HTMLElement>) => {
      const touch = event.touches[0]
      if (!touch || event.touches.length !== 1) {
        return
      }
      if (
        event.target instanceof Element &&
        event.target.closest('input, textarea, [data-drawer-gesture-ignore]')
      ) {
        return
      }
      // 指针通道已经在跑就不重复开一条
      if (drag.current) {
        return
      }
      begin(touch.clientX, touch.clientY, -1)
    },
    [begin],
  )

  const onTouchMove = useCallback(
    (event: ReactTouchEvent<HTMLElement>) => {
      const touch = event.touches[0]
      if (!touch || !drag.current || drag.current.id !== -1) {
        return
      }
      moveTo(touch.clientX, touch.clientY, -1)
    },
    [moveTo],
  )

  const onTouchEnd = useCallback(
    (event: ReactTouchEvent<HTMLElement>) => {
      const touch = event.changedTouches[0]
      if (!touch) {
        return
      }
      end(touch.clientX, -1)
    },
    [end],
  )

  const onTouchCancel = useCallback(() => cancel(-1), [cancel])

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

  return {
    onPointerDown,
    onPointerMove,
    onPointerUp,
    onPointerCancel,
    onTouchStart,
    onTouchMove,
    onTouchEnd,
    onTouchCancel,
  }
}
