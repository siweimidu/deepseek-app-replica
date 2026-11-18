import { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { usePredictiveBack } from '../../app/backGesture.js'
import { useTranslate } from '../../i18n/index.js'
import { showToast } from '../base/toastState.js'
import styles from './AvatarEditor.module.css'

/** 取景框直径，与样式里的 .hole 半径保持一致 */
const STAGE = 288
const OUTPUT = 320

type Point = { x: number; y: number }

const distance = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y)

/**
 * 头像裁切页：独立整页（portal 到 body，铺满屏幕），圆形取景框里拖动 / 双指缩放，
 * 确认后按取景框范围裁成正方形保存，展示处再按圆形显示，避免导出出现黑角。
 */
export const AvatarEditor = ({
  file,
  onCancel,
  onDone,
}: {
  file: File
  onCancel: () => void
  onDone: (dataUrl: string) => void
}) => {
  const t = useTranslate()
  const [image, setImage] = useState<HTMLImageElement | null>(null)
  const [scale, setScale] = useState(1)
  const [offset, setOffset] = useState<Point>({ x: 0, y: 0 })
  const pointers = useRef(new Map<number, Point>())
  const stage = useRef<HTMLDivElement>(null)
  const gesture = useRef<{ distance: number; scale: number } | null>(null)
  usePredictiveBack(stage, onCancel)

  useEffect(() => {
    const url = URL.createObjectURL(file)
    const element = new Image()
    element.onload = () => setImage(element)
    element.onerror = () => showToast({ key: 'accountAvatarFailed', type: 'error' })
    element.src = url
    return () => URL.revokeObjectURL(url)
  }, [file])

  // 让图片最短边刚好盖住取景框，初始不留空隙。
  const fit = image ? STAGE / Math.min(image.width, image.height) : 1
  const width = image ? image.width * fit * scale : 0
  const height = image ? image.height * fit * scale : 0
  const limit = {
    x: Math.max(0, (width - STAGE) / 2),
    y: Math.max(0, (height - STAGE) / 2),
  }

  const clampOffset = useCallback(
    (value: Point) => ({
      x: Math.min(limit.x, Math.max(-limit.x, value.x)),
      y: Math.min(limit.y, Math.max(-limit.y, value.y)),
    }),
    [limit.x, limit.y]
  )

  const zoomTo = (next: number) => setScale(Math.min(4, Math.max(1, next)))

  const save = () => {
    if (!image) {
      return
    }
    const canvas = document.createElement('canvas')
    canvas.width = OUTPUT
    canvas.height = OUTPUT
    const context = canvas.getContext('2d')
    if (!context) {
      return
    }
    const ratio = OUTPUT / STAGE
    const drawWidth = width * ratio
    const drawHeight = height * ratio
    context.drawImage(
      image,
      OUTPUT / 2 + offset.x * ratio - drawWidth / 2,
      OUTPUT / 2 + offset.y * ratio - drawHeight / 2,
      drawWidth,
      drawHeight
    )
    onDone(canvas.toDataURL('image/jpeg', 0.86))
  }

  return createPortal(
    <div className={styles.page} role="dialog" aria-modal="true">
      <header className={styles.header}>
        <button type="button" className={styles.action} onClick={onCancel}>
          {t('cancel')}
        </button>
        <span className={styles.heading}>{t('accountAvatarAdjust')}</span>
        <button type="button" className={styles.action} data-primary="" onClick={save}>
          {t('accountAvatarDone')}
        </button>
      </header>
      <div
        ref={stage}
        className={styles.stage}
        onPointerDown={(event) => {
          event.currentTarget.setPointerCapture(event.pointerId)
          pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY })
          if (pointers.current.size === 2) {
            const [first, second] = [...pointers.current.values()]
            gesture.current = { distance: distance(first, second), scale }
          }
        }}
        onPointerMove={(event) => {
          const previous = pointers.current.get(event.pointerId)
          if (!previous) {
            return
          }
          pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY })
          if (pointers.current.size >= 2 && gesture.current) {
            const [first, second] = [...pointers.current.values()]
            zoomTo(gesture.current.scale * (distance(first, second) / (gesture.current.distance || 1)))
            return
          }
          setOffset((current) =>
            clampOffset({
              x: current.x + (event.clientX - previous.x),
              y: current.y + (event.clientY - previous.y),
            })
          )
        }}
        onPointerUp={(event) => {
          pointers.current.delete(event.pointerId)
          if (pointers.current.size < 2) {
            gesture.current = null
          }
        }}
        onPointerCancel={() => {
          pointers.current.clear()
          gesture.current = null
        }}
        onWheel={(event) => zoomTo(scale * (event.deltaY > 0 ? 0.94 : 1.06))}
      >
        <span className={styles.hole} aria-hidden="true" />
        {image ? (
          <img
            className={styles.image}
            src={image.src}
            alt=""
            draggable={false}
            style={{
              width,
              height,
              transform: `translate(calc(-50% + ${offset.x}px), calc(-50% + ${offset.y}px))`,
            }}
          />
        ) : null}
      </div>
      <p className={styles.hint}>{t('accountAvatarHint')}</p>
    </div>,
    document.body
  )
}
