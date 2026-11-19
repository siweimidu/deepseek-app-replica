import { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { usePredictiveBack } from '../../app/backGesture.js'
import { addDraftFiles } from '../../services/chat/drafts.js'
import { useChatStore } from '../../services/chat/store.js'
import { useSettings } from '../../services/settings.js'
import { showToast } from '../base/toastState.js'
import { ImageCropper } from './ImageCropper.js'
import { closeImageViewer, useImageViewer } from './imageViewerState.js'
import styles from './ImageViewer.module.css'

type Transform = { scale: number; x: number; y: number }

type Point = { clientX: number; clientY: number }

const MIN_SCALE = 1
const MAX_SCALE = 4
const CLOSE_DRAG = 130
/** 短按判定：位移与时长都要小 */
const TAP_MAX_MOVE = 8
const TAP_MAX_MS = 260
/** 两次短按之间小于这个间隔算双击 */
const DOUBLE_TAP_MS = 350
const DOUBLE_TAP_SCALE = 2.5

const distance = (a: Point, b: Point) => Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY)

const IDENTITY: Transform = { scale: 1, x: 0, y: 0 }

/**
 * 全屏看图：双指缩放、双击放大、放大后拖动、未放大时下拉关闭。
 * 双击判定放在「短按结束」上，避免与拖动结束的重置互相干扰。
 */
export const ImageViewer = () => {
  const { open, src } = useImageViewer()
  const [transform, setTransform] = useState<Transform>(IDENTITY)
  const [dragging, setDragging] = useState(false)
  const [cropping, setCropping] = useState(false)
  const transformRef = useRef<Transform>(IDENTITY)
  const stageRef = useRef<HTMLDivElement>(null)
  const gesture = useRef({
    mode: 'none' as 'none' | 'pan' | 'pinch',
    startX: 0,
    startY: 0,
    startedAt: 0,
    moved: false,
    tapX: 0,
    tapY: 0,
    startDistance: 0,
    startScale: 1,
    base: IDENTITY as Transform,
    lastTapAt: 0,
  })

  const apply = useCallback((next: Transform) => {
    transformRef.current = next
    setTransform(next)
  }, [])

  useEffect(() => {
    if (!open) {
      apply(IDENTITY)
      return
    }
    gesture.current.lastTapAt = 0
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        closeImageViewer()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, apply])

  usePredictiveBack(stageRef, closeImageViewer, open)

  if (!open || !src) {
    return null
  }

  const clampScale = (value: number) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, value))

  /** 以某个点为中心缩放 */
  const zoomAt = (scale: number, tapX: number, tapY: number) => {
    const rect = stageRef.current?.getBoundingClientRect()
    if (!rect) {
      apply(IDENTITY)
      return
    }
    if (scale <= 1.02) {
      apply(IDENTITY)
      return
    }
    const originX = tapX - rect.left - rect.width / 2
    const originY = tapY - rect.top - rect.height / 2
    apply({ scale, x: -originX * (scale - 1), y: -originY * (scale - 1) })
  }

  const onTouchStart = (event: React.TouchEvent<HTMLDivElement>) => {
    const state = gesture.current
    if (event.touches.length >= 2) {
      state.mode = 'pinch'
      state.startDistance = distance(event.touches[0], event.touches[1])
      state.startScale = transformRef.current.scale
      state.base = transformRef.current
      state.moved = true
      setDragging(true)
      return
    }
    const touch = event.touches[0]
    state.mode = 'pan'
    state.startX = touch.clientX
    state.startY = touch.clientY
    state.startedAt = Date.now()
    state.moved = false
    state.tapX = touch.clientX
    state.tapY = touch.clientY
    state.base = transformRef.current
    setDragging(true)
  }

  const onTouchMove = (event: React.TouchEvent<HTMLDivElement>) => {
    const state = gesture.current
    if (state.mode === 'pinch' && event.touches.length >= 2) {
      event.preventDefault()
      const ratio = distance(event.touches[0], event.touches[1]) / Math.max(1, state.startDistance)
      const scale = clampScale(state.startScale * ratio)
      apply({ ...transformRef.current, scale })
      return
    }
    if (state.mode !== 'pan' || event.touches.length !== 1) {
      return
    }
    const dx = event.touches[0].clientX - state.startX
    const dy = event.touches[0].clientY - state.startY
    if (!state.moved && Math.abs(dx) + Math.abs(dy) > TAP_MAX_MOVE) {
      state.moved = true
    }
    if (state.base.scale > 1.02) {
      event.preventDefault()
      apply({ scale: state.base.scale, x: state.base.x + dx, y: state.base.y + dy })
      return
    }
    if (dy > 0) {
      event.preventDefault()
      apply({ scale: 1, x: 0, y: dy })
    }
  }

  const onTouchEnd = () => {
    const state = gesture.current
    const current = transformRef.current
    const mode = state.mode
    state.mode = 'none'
    setDragging(false)

    if (mode === 'pinch') {
      if (current.scale <= 1.02) {
        apply(IDENTITY)
      }
      return
    }
    if (mode !== 'pan') {
      return
    }

    const quick = Date.now() - state.startedAt < TAP_MAX_MS
    if (!state.moved && quick) {
      const now = Date.now()
      if (now - state.lastTapAt < DOUBLE_TAP_MS) {
        state.lastTapAt = 0
        zoomAt(current.scale > 1.2 ? 1 : DOUBLE_TAP_SCALE, state.tapX, state.tapY)
        return
      }
      state.lastTapAt = now
      // 单指轻点不做事，保持当前缩放
      if (current.scale <= 1.02) {
        apply(IDENTITY)
      }
      return
    }

    if (current.scale <= 1.02 && current.y > CLOSE_DRAG) {
      closeImageViewer()
      return
    }
    if (current.scale <= 1.02) {
      apply(IDENTITY)
    }
  }

  return createPortal(
    <div
      ref={stageRef}
      className={styles.stage}
      data-dragging={dragging ? '' : undefined}
      role="dialog"
      aria-modal="true"
      aria-label="图片预览"
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEnd}
      onTouchCancel={onTouchEnd}
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          closeImageViewer()
        }
      }}
      onWheel={(event) => {
        event.preventDefault()
        apply({ ...transformRef.current, scale: clampScale(transformRef.current.scale - event.deltaY / 400) })
      }}
    >
      <img
        className={styles.image}
        src={src}
        alt=""
        draggable={false}
        style={{
          transform: `translate3d(${transform.x}px, ${transform.y}px, 0) scale(${transform.scale})`,
          transition: dragging ? 'none' : 'transform 200ms cubic-bezier(0.22, 1, 0.36, 1)',
        }}
      />
      <button
        type="button"
        className={styles.crop}
        aria-label="裁剪"
        onClick={() => setCropping(true)}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinecap="round"
        >
          <path d="M6 2v10a2 2 0 002 2h10" />
          <path d="M14 18V8a2 2 0 00-2-2H2" />
        </svg>
      </button>
      <button type="button" className={styles.close} aria-label="关闭" onClick={closeImageViewer}>
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
        >
          <path d="M5.5 5.5l9 9M14.5 5.5l-9 9" />
        </svg>
      </button>
      {cropping ? (
        <ImageCropper
          src={src}
          fileName="image"
          onCancel={() => setCropping(false)}
          onDone={(file) => {
            setCropping(false)
            const sessionId = useChatStore.getState().activeId
            const apiKey = useSettings.getState().apiKey ?? ''
            const error = addDraftFiles(sessionId, [file], apiKey)
            if (error) {
              showToast(error)
              return
            }
            closeImageViewer()
            showToast('裁剪完成，已添加到输入框')
          }}
        />
      ) : null}
    </div>,
    document.body
  )
}
