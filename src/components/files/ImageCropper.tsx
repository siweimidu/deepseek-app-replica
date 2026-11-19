import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { usePredictiveBack } from '../../app/backGesture.js'
import { cropToFile, loadSource, type CropRect } from './imageCrop.js'
import styles from './ImageCropper.module.css'

type Props = {
  /** 图片地址（blob:/data:/http） */
  src: string
  fileName?: string
  onCancel: () => void
  onDone: (file: File) => void
}

type DragMode = 'none' | 'move' | 'nw' | 'ne' | 'sw' | 'se'

const MIN_SIZE = 48

/** 图片裁剪器：拖动裁剪框、四角缩放，支持自由/1:1/4:3/16:9 */
export const ImageCropper = ({ src, fileName, onCancel, onDone }: Props) => {
  const stageRef = useRef<HTMLDivElement>(null)
  const [image, setImage] = useState<HTMLImageElement | null>(null)
  const [box, setBox] = useState({ width: 0, height: 0, left: 0, top: 0 })
  const [rect, setRect] = useState<CropRect>({ x: 0, y: 0, width: 0, height: 0 })
  const [ratio, setRatio] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const drag = useRef<{
    mode: DragMode
    startX: number
    startY: number
    origin: CropRect
  }>({ mode: 'none', startX: 0, startY: 0, origin: { x: 0, y: 0, width: 0, height: 0 } })

  usePredictiveBack(stageRef, onCancel, true)

  useEffect(() => {
    let cancelled = false
    void loadSource(src).then((loaded) => {
      if (!cancelled) {
        setImage(loaded)
      }
    })
    return () => {
      cancelled = true
    }
  }, [src])

  // 图片在舞台内的显示框（等比缩放）
  useEffect(() => {
    const measure = () => {
      const stage = stageRef.current
      if (!stage || !image) {
        return
      }
      const stageRect = stage.getBoundingClientRect()
      const maxWidth = stageRect.width - 32
      const maxHeight = stageRect.height - 160
      const scale = Math.min(maxWidth / image.naturalWidth, maxHeight / image.naturalHeight, 1)
      const width = Math.round(image.naturalWidth * scale)
      const height = Math.round(image.naturalHeight * scale)
      const next = {
        width,
        height,
        left: Math.round((stageRect.width - width) / 2),
        top: Math.round((stageRect.height - height) / 2),
      }
      setBox(next)
      setRect((current) => {
        if (current.width > 0) {
          return current
        }
        const size = Math.min(width, height) * 0.8
        return { x: (width - size) / 2, y: (height - size) / 2, width: size, height: size }
      })
    }
    measure()
    window.addEventListener('resize', measure)
    return () => window.removeEventListener('resize', measure)
  }, [image])

  const applyRatio = (next: number | null) => {
    setRatio(next)
    if (!next) {
      return
    }
    setRect((current) => {
      const centerX = current.x + current.width / 2
      const centerY = current.y + current.height / 2
      let width = current.width
      let height = width / next
      if (height > box.height) {
        height = box.height
        width = height * next
      }
      if (width > box.width) {
        width = box.width
        height = width / next
      }
      const x = Math.min(Math.max(0, centerX - width / 2), box.width - width)
      const y = Math.min(Math.max(0, centerY - height / 2), box.height - height)
      return { x, y, width, height }
    })
  }

  const startDrag = (mode: DragMode) => (event: React.TouchEvent | React.PointerEvent) => {
    const point = 'touches' in event ? event.touches[0] : event
    drag.current = { mode, startX: point.clientX, startY: point.clientY, origin: rect }
  }

  const onMove = (event: React.TouchEvent | React.PointerEvent) => {
    if (drag.current.mode === 'none') {
      return
    }
    const point = 'touches' in event ? event.touches[0] : event
    const dx = point.clientX - drag.current.startX
    const dy = point.clientY - drag.current.startY
    const origin = drag.current.origin
    const mode = drag.current.mode

    if (mode === 'move') {
      setRect({
        ...origin,
        x: Math.min(Math.max(0, origin.x + dx), box.width - origin.width),
        y: Math.min(Math.max(0, origin.y + dy), box.height - origin.height),
      })
      return
    }

    // 四角缩放：先算新边界，再按比例（若锁定）修正
    let left = origin.x
    let top = origin.y
    let right = origin.x + origin.width
    let bottom = origin.y + origin.height
    if (mode === 'nw' || mode === 'sw') {
      left = Math.min(right - MIN_SIZE, Math.max(0, origin.x + dx))
    }
    if (mode === 'ne' || mode === 'se') {
      right = Math.max(left + MIN_SIZE, Math.min(box.width, origin.x + origin.width + dx))
    }
    if (mode === 'nw' || mode === 'ne') {
      top = Math.min(bottom - MIN_SIZE, Math.max(0, origin.y + dy))
    }
    if (mode === 'sw' || mode === 'se') {
      bottom = Math.max(top + MIN_SIZE, Math.min(box.height, origin.y + origin.height + dy))
    }
    let width = right - left
    let height = bottom - top
    if (ratio) {
      if (width / height > ratio) {
        width = height * ratio
        if (mode === 'nw' || mode === 'sw') {
          left = right - width
        } else {
          right = left + width
        }
      } else {
        height = width / ratio
        if (mode === 'nw' || mode === 'ne') {
          top = bottom - height
        } else {
          bottom = top + height
        }
      }
    }
    setRect({ x: left, y: top, width, height })
  }

  const endDrag = () => {
    drag.current.mode = 'none'
  }

  const confirm = async () => {
    if (!image || busy || rect.width < MIN_SIZE) {
      return
    }
    setBusy(true)
    try {
      const scale = image.naturalWidth / box.width
      const file = await cropToFile(
        image,
        {
          x: rect.x * scale,
          y: rect.y * scale,
          width: rect.width * scale,
          height: rect.height * scale,
        },
        { fileName }
      )
      onDone(file)
    } finally {
      setBusy(false)
    }
  }

  return createPortal(
    <div
      ref={stageRef}
      className={styles.stage}
      role="dialog"
      aria-modal="true"
      aria-label="裁剪图片"
      onTouchMove={onMove}
      onTouchEnd={endDrag}
      onTouchCancel={endDrag}
      onPointerMove={(event) => {
        if (drag.current.mode !== 'none') {
          onMove(event)
        }
      }}
      onPointerUp={endDrag}
    >
      <div className={styles.canvas} style={{ left: box.left, top: box.top, width: box.width, height: box.height }}>
        {image ? <img src={src} alt="" draggable={false} /> : null}
        <div className={styles.mask} />
        <div
          className={styles.rect}
          style={{ left: rect.x, top: rect.y, width: rect.width, height: rect.height }}
          onTouchStart={startDrag('move')}
          onPointerDown={startDrag('move')}
        >
          {(['nw', 'ne', 'sw', 'se'] as const).map((corner) => (
            <span
              key={corner}
              className={styles[corner]}
              onTouchStart={(event) => {
                event.stopPropagation()
                startDrag(corner)(event)
              }}
              onPointerDown={(event) => {
                event.stopPropagation()
                startDrag(corner)(event)
              }}
            />
          ))}
        </div>
      </div>

      <div className={styles.ratios}>
        {[
          { label: '自由', value: null },
          { label: '1:1', value: 1 },
          { label: '4:3', value: 4 / 3 },
          { label: '16:9', value: 16 / 9 },
        ].map((item) => (
          <button
            key={item.label}
            type="button"
            className={styles.ratio}
            data-active={ratio === item.value ? '' : undefined}
            onClick={() => applyRatio(item.value)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className={styles.actions}>
        <button type="button" className={styles.cancel} onClick={onCancel}>
          取消
        </button>
        <button type="button" className={styles.confirm} onClick={confirm} disabled={busy}>
          {busy ? '处理中…' : '完成'}
        </button>
      </div>
    </div>,
    document.body
  )
}
