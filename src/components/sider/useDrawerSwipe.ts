import { useEffect, useRef } from 'react'
import { android } from '../../app/android.js'
import { closeMobileSider, openMobileSider, useMobileSider } from './mobileSiderState.js'

/**
 * 抽屉手势：唯一的一套实现。
 *
 * 只用触摸事件（WebView 里 pointer 事件会被合成器取消），一个状态机：
 *   idle → pending（等方向判定）→ dragging（跟手）→ settling（动画到终点）
 * 结束时一定把内联变量清干净，并且先从当前位移过渡到终点、再切状态，
 * 这样既不会卡在半途，也不会出现跳变（闪现）。
 */

const SLOP = 8
const DIRECTION_RATIO = 1.15
const CLOSE_PX = 22
const OPEN_RATIO = 0.12

type Phase = 'idle' | 'pending' | 'dragging' | 'settling'

type Track = {
  phase: Phase
  startX: number
  startY: number
  width: number
  openedAtStart: boolean
  progress: number
  timer: number
}

export const useDrawerSwipe = (frameRef: { current: HTMLElement | null }) => {
  const track = useRef<Track | null>(null)

  useEffect(() => {
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
    }

    /** 从当前位置过渡到终点，动画结束后再切状态，再清内联值 */
    const settle = (close: boolean) => {
      const state = track.current
      if (!state) {
        return
      }
      state.phase = 'settling'
      const target = close ? 0 : 1
      frameOf()?.removeAttribute('data-drawer-dragging')
      setProgress(target)
      window.clearTimeout(state.timer)
      state.timer = window.setTimeout(() => {
        if (close) {
          closeMobileSider()
        } else {
          openMobileSider()
        }
        clearInline()
        track.current = null
      }, 200)
    }

    const onStart = (event: TouchEvent) => {
      const touch = event.touches[0]
      if (!touch || event.touches.length > 1) {
        return
      }
      if (
        event.target instanceof Element &&
        event.target.closest('input, textarea, [data-drawer-gesture-ignore]')
      ) {
        return
      }
      const frame = frameOf()
      if (!frame) {
        return
      }
      const drawer = frame.querySelector<HTMLElement>('[data-android-drawer]')
      if (!drawer) {
        return
      }
      track.current = {
        phase: 'pending',
        startX: touch.clientX,
        startY: touch.clientY,
        width: drawer.offsetWidth || window.innerWidth,
        openedAtStart: useMobileSider.getState().open,
        progress: useMobileSider.getState().open ? 1 : 0,
        timer: 0,
      }
    }

    const onMove = (event: TouchEvent) => {
      const state = track.current
      const touch = event.touches[0]
      if (!state || !touch || state.phase === 'settling') {
        return
      }
      const dx = touch.clientX - state.startX
      const dy = touch.clientY - state.startY

      if (state.phase === 'pending') {
        if (Math.abs(dx) < SLOP && Math.abs(dy) < SLOP) {
          return
        }
        const horizontal = Math.abs(dx) > Math.abs(dy) * DIRECTION_RATIO
        // 打开状态下两个方向都接受（往左=收起），关闭状态下只接受往右（往左=拉出）
        const valid = state.openedAtStart ? horizontal : horizontal && dx > 0
        if (!valid) {
          track.current = null
          return
        }
        state.phase = 'dragging'
        frameOf()?.setAttribute('data-drawer-dragging', '')
      }

      state.progress = state.openedAtStart ? 1 + dx / state.width : dx / state.width
      setProgress(state.progress)
    }

    const onEnd = () => {
      const state = track.current
      if (!state || state.phase !== 'dragging') {
        track.current = null
        return
      }
      const travelled = (state.progress - (state.openedAtStart ? 1 : 0)) * state.width
      if (state.openedAtStart) {
        // 往左带过 22px，或已经收过 1/5，都算要关闭
        settle(travelled < -CLOSE_PX || state.progress < 0.8)
      } else {
        settle(state.progress > OPEN_RATIO)
      }
    }

    const onCancel = () => {
      const state = track.current
      if (!state) {
        return
      }
      if (state.phase === 'dragging') {
        settle(state.openedAtStart)
      } else {
        track.current = null
      }
    }

    // 绑在 document 上：不依赖 frame 何时挂载，任何时候都不会失效
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
    }
  }, [frameRef])

  // 状态自愈：任何一次开合结束后都不允许残留半途的进度
  useEffect(
    () =>
      useMobileSider.subscribe(() => {
        const frame = frameRef.current
        if (!frame) {
          return
        }
        if (!frame.hasAttribute('data-drawer-dragging')) {
          frame.style.removeProperty('--drawer-progress')
        }
      }),
    [frameRef],
  )
}
