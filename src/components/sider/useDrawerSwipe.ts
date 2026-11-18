import { useEffect, useRef } from 'react'
import { android } from '../../app/android.js'
import { closeMobileSider, openMobileSider, useMobileSider } from './mobileSiderState.js'

/**
 * 侧边栏横滑（最终版，极简）
 *
 * 规则：
 *   对话页 —— 向「左」横滑拉出侧边栏
 *   侧边栏 —— 向「右」横滑回到对话
 *
 * 设计取舍（都是踩过的坑）：
 * 1. touch 和 pointer 两套事件都听，谁先到算谁；一套被合成器取消时另一套还能用。
 * 2. 状态切换**不碰任何 DOM**：直接调 store。会不会动只取决于状态，不取决于拿没拿到元素。
 *    （之前 settle() 里先判元素存在再切状态，元素取不到就整个失效，表现就是"怎么滑都没反应"。）
 * 3. 跟手只是锦上添花：拿不到 frame 就跳过跟手，松手依然会切换。
 * 4. 横向/纵向判定用 1.2 倍比，纵向滑动完全放行。
 */

const SLOP = 8
const RATIO = 1.2
const TRIGGER_PX = 26

type Phase = 'idle' | 'pending' | 'opening' | 'closing'

type Track = {
  phase: Phase
  x: number
  y: number
  lastDx: number
  width: number
  opened: boolean
  consumed: boolean
}

export const useDrawerSwipe = (frameRef: { current: HTMLElement | null }) => {
  const track = useRef<Track | null>(null)

  useEffect(() => {
    if (!android) {
      return
    }

    const node = () =>
      frameRef.current ??
      document.querySelector<HTMLElement>('[data-android-drawer]')?.parentElement ??
      null

    const paint = (progress: number) => {
      const element = node()
      if (!element) {
        return
      }
      element.setAttribute('data-drawer-dragging', '')
      element.style.setProperty('--drawer-progress', String(Math.max(0, Math.min(1, progress))))
    }

    const clear = () => {
      const element = node()
      element?.removeAttribute('data-drawer-dragging')
      element?.style.removeProperty('--drawer-progress')
    }

    /** 只改状态，不碰 DOM —— 这是"能不能切换"的唯一决定因素 */
    const apply = (open: boolean) => {
      clear()
      if (open) {
        openMobileSider()
      } else {
        closeMobileSider()
      }
    }

    const start = (x: number, y: number) => {
      const element = node()
      const drawer = element?.querySelector<HTMLElement>('[data-android-drawer]')
      track.current = {
        phase: 'pending',
        x,
        y,
        lastDx: 0,
        width: drawer?.offsetWidth || window.innerWidth,
        opened: useMobileSider.getState().open,
        consumed: false,
      }
    }

    const move = (x: number, y: number) => {
      const state = track.current
      if (!state || state.consumed) {
        return
      }
      const dx = x - state.x
      const dy = y - state.y
      state.lastDx = dx

      if (state.phase === 'pending') {
        if (Math.abs(dx) < SLOP && Math.abs(dy) < SLOP) {
          return
        }
        if (Math.abs(dx) <= Math.abs(dy) * RATIO) {
          track.current = null
          return
        }
        // 硬规则方向：关闭时只认向左，打开时只认向右
        if (!state.opened && dx < 0) {
          state.phase = 'opening'
        } else if (state.opened && dx > 0) {
          state.phase = 'closing'
        } else {
          track.current = null
          return
        }
      }

      const progress =
        state.phase === 'opening' ? -dx / state.width : 1 - dx / state.width
      paint(progress)

      // 越过阈值立刻切换：不等抬手，用户拖过一点就能看到结果
      if (Math.abs(dx) >= TRIGGER_PX && !state.consumed) {
        state.consumed = true
        track.current = null
        apply(state.phase === 'opening')
      }
    }

    const finish = () => {
      const state = track.current
      track.current = null
      if (!state || state.consumed || state.phase === 'pending') {
        return
      }
      // 没到阈值：回到拖动前的状态
      apply(state.opened)
    }

    const touchStart = (event: TouchEvent) => {
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
      start(touch.clientX, touch.clientY)
    }
    const touchMove = (event: TouchEvent) => {
      const touch = event.touches[0]
      if (touch) {
        move(touch.clientX, touch.clientY)
      }
    }

    const pointerStart = (event: PointerEvent) => {
      if (event.pointerType === 'mouse') {
        return
      }
      if (
        event.target instanceof Element &&
        event.target.closest('input, textarea, [data-drawer-gesture-ignore]')
      ) {
        return
      }
      start(event.clientX, event.clientY)
    }
    const pointerMove = (event: PointerEvent) => {
      if (event.pointerType !== 'mouse') {
        move(event.clientX, event.clientY)
      }
    }

    document.addEventListener('touchstart', touchStart, { passive: true })
    document.addEventListener('touchmove', touchMove, { passive: true })
    document.addEventListener('touchend', finish, { passive: true })
    document.addEventListener('touchcancel', finish, { passive: true })
    document.addEventListener('pointerdown', pointerStart, { passive: true })
    document.addEventListener('pointermove', pointerMove, { passive: true })
    document.addEventListener('pointerup', finish, { passive: true })
    document.addEventListener('pointercancel', finish, { passive: true })

    return () => {
      document.removeEventListener('touchstart', touchStart)
      document.removeEventListener('touchmove', touchMove)
      document.removeEventListener('touchend', finish)
      document.removeEventListener('touchcancel', finish)
      document.removeEventListener('pointerdown', pointerStart)
      document.removeEventListener('pointermove', pointerMove)
      document.removeEventListener('pointerup', finish)
      document.removeEventListener('pointercancel', finish)
      clear()
    }
  }, [frameRef])

  // 不变量：打开 ⇒ 进度恒为 1；关闭 ⇒ 不残留内联进度（拖拽中不干预）
  useEffect(
    () =>
      useMobileSider.subscribe((state) => {
        const element =
          frameRef.current ??
          document.querySelector<HTMLElement>('[data-android-drawer]')?.parentElement ??
          null
        if (!element || element.hasAttribute('data-drawer-dragging')) {
          return
        }
        if (state.open) {
          element.style.setProperty('--drawer-progress', '1')
        } else {
          element.style.removeProperty('--drawer-progress')
        }
      }),
    [frameRef],
  )
}
