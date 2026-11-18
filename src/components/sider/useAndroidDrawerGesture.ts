import { useRef, type PointerEvent } from 'react'
import { android } from '../../app/android.js'
import { closeMobileSider, openMobileSider, useMobileSider } from './mobileSiderState.js'

const clamp = (value: number) => Math.max(0, Math.min(1, value))
const slop = 4

type Gesture = {
  id: number
  x: number
  y: number
  edge: number
  startedOpen: boolean
  start: number
  current: number
  captured: boolean
  previousX: number
  previousTime: number
  velocity: number
}

export const useAndroidDrawerGesture = () => {
  const gesture = useRef<Gesture | null>(null)

  const onPointerDownCapture = (event: PointerEvent<HTMLDivElement>) => {
    if (
      !android ||
      !event.isPrimary ||
      event.pointerType === 'mouse' ||
      (document.documentElement.hasAttribute('data-keyboard') &&
        !useMobileSider.getState().open) ||
      (event.target instanceof Element &&
        event.target.closest('input, textarea, [data-drawer-gesture-ignore]'))
    ) {
      return
    }
    const frame = event.currentTarget
    const drawer = frame.querySelector<HTMLElement>('[data-android-drawer]')
    const main = frame.querySelector('main')
    if (!drawer || !main) {
      return
    }
    const edge = drawer.offsetWidth
    const start = clamp(
      (main.getBoundingClientRect().left - frame.getBoundingClientRect().left) / edge
    )
    gesture.current = {
      id: event.pointerId,
      x: event.clientX,
      y: event.clientY,
      edge,
      startedOpen: useMobileSider.getState().open,
      start,
      current: start,
      captured: false,
      previousX: event.clientX,
      previousTime: event.timeStamp,
      velocity: 0,
    }
  }

  const onPointerMoveCapture = (event: PointerEvent<HTMLDivElement>) => {
    const drag = gesture.current
    if (!drag || drag.id !== event.pointerId) {
      return
    }
    const frame = event.currentTarget
    const dx = event.clientX - drag.x
    if (!drag.captured) {
      const dy = Math.abs(event.clientY - drag.y)
      if (dy > slop && dy >= Math.abs(dx)) {
        gesture.current = null
        return
      }
      if (Math.abs(dx) < slop || (drag.start === 0 && dx < 0) || (drag.start === 1 && dx > 0)) {
        return
      }
      drag.captured = true
      frame.dataset.drawerDragging = ''
      frame.setPointerCapture(event.pointerId)
    }
    const distance = dx > 0 ? Math.max(0, dx - slop) : Math.min(0, dx + slop)
    drag.current = clamp(drag.start + (1.031 * distance) / drag.edge)
    frame.style.setProperty('--drawer-progress', String(drag.current))
    if (event.timeStamp > drag.previousTime) {
      drag.velocity = (event.clientX - drag.previousX) / (event.timeStamp - drag.previousTime)
    }
    drag.previousX = event.clientX
    drag.previousTime = event.timeStamp
  }

  const settle = (event: PointerEvent<HTMLDivElement>, cancelled: boolean) => {
    const drag = gesture.current
    if (!drag || drag.id !== event.pointerId) {
      return
    }
    gesture.current = null
    if (!drag.captured) {
      return
    }
    const frame = event.currentTarget
    const flick = event.timeStamp - drag.previousTime < 100 && Math.abs(drag.velocity) > 0.32
    // 用"实际移动了多少像素"判断，而不是进度：轻轻一滑只有 30px，按进度算会被判成保持打开
    const travelled = (drag.current - drag.start) * drag.edge
    const open = cancelled
      ? drag.startedOpen
      : flick
        ? drag.velocity > 0
        : drag.startedOpen
          ? travelled > -24
          : travelled > drag.edge * 0.12
    frame.dataset.drawerOpen = String(open)
    delete frame.dataset.drawerDragging
    // Let the transition start at the last rendered drag position.
    frame.getBoundingClientRect()
    frame.style.removeProperty('--drawer-progress')
    event.preventDefault()
    if (open) {
      openMobileSider()
    } else {
      closeMobileSider()
    }
  }

  return {
    onPointerDownCapture,
    onPointerMoveCapture,
    onPointerUpCapture: (event: PointerEvent<HTMLDivElement>) => settle(event, false),
    onPointerCancelCapture: (event: PointerEvent<HTMLDivElement>) => settle(event, true),
    onLostPointerCapture: (event: PointerEvent<HTMLDivElement>) => {
      if (event.target === event.currentTarget) {
        settle(event, true)
      }
    },
  }
}
