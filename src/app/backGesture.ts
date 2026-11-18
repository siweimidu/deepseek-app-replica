import { useEffect, useRef, type RefObject } from 'react'

export type BackGestureState = 'start' | 'progress' | 'cancel' | 'invoked'

type Listener = (state: BackGestureState, progress: number) => void

/**
 * Android 14 起的预测性返回：手势进行中系统持续回调进度，前端据此实时位移当前界面；
 * 只有最后的 invoked 才真正执行返回。多层界面用栈注册，最上层（最后挂载）消费手势，
 * 关闭后自动回退到下一层。
 */
const stack: Listener[] = []
let installed = false

/** 原生在 invoked 之后会读这个标记，决定还要不要把返回交给页面自己处理。 */
const markConsumed = () => {
  ;(window as Window & { __dshConsumedBack?: boolean }).__dshConsumedBack = true
  window.setTimeout(() => {
    ;(window as Window & { __dshConsumedBack?: boolean }).__dshConsumedBack = false
  }, 0)
}

const install = () => {
  if (installed || typeof window === 'undefined') {
    return
  }
  installed = true
  window.addEventListener('android-back-gesture', (event) => {
    const detail = (event as CustomEvent<{ state?: BackGestureState; progress?: number }>).detail
    if (!detail?.state) {
      return
    }
    const listener = stack[stack.length - 1]
    if (!listener) {
      return
    }
    if (detail.state === 'invoked') {
      markConsumed()
    }
    listener(detail.state, detail.progress ?? 0)
  })
}

export const claimBackGesture = (listener: Listener) => {
  install()
  stack.push(listener)
  return () => {
    const index = stack.lastIndexOf(listener)
    if (index >= 0) {
      stack.splice(index, 1)
    }
  }
}

/**
 * 把预测性返回进度写到元素的 --back-progress 上，位移与缩放交给样式决定。
 * 手势取消时复位，手势完成时复位并执行返回。
 */
export const usePredictiveBack = (
  ref: RefObject<HTMLElement | null>,
  onBack: () => void,
  active = true
) => {
  const handler = useRef(onBack)
  handler.current = onBack

  useEffect(() => {
    if (!active) {
      return
    }
    const reset = () => {
      const element = ref.current
      if (!element) {
        return
      }
      element.removeAttribute('data-back')
      element.style.setProperty('--back-progress', '0')
    }
    // 上一次手势如果被系统打断，偏移会留在元素上：先复位，避免整页偏着导致点击错位
    reset()
    return claimBackGesture((state, progress) => {
      const element = ref.current
      if (!element) {
        return
      }
      if (state === 'start') {
        element.setAttribute('data-back', 'active')
        element.style.setProperty('--back-progress', '0')
      } else if (state === 'progress') {
        element.setAttribute('data-back', 'active')
        element.style.setProperty('--back-progress', String(Math.min(1, Math.max(0, progress))))
      } else if (state === 'cancel') {
        reset()
      } else {
        reset()
        handler.current()
      }
    })
  }, [active, ref])
}
