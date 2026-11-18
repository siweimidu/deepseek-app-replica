import { animate, type AnimationPlaybackControls } from 'motion'

/**
 * 弹簧参数（参考 motion / framer-motion 的物理模型）
 * 刚度越高起手越快，阻尼越高收尾越干脆。
 */
export const DRAWER_SPRING = { type: 'spring', stiffness: 820, damping: 38, mass: 0.7 } as const
export const CARD_SPRING = { type: 'spring', stiffness: 600, damping: 34, mass: 0.7 } as const

type Options = {
  velocity?: number
  onUpdate: (value: number) => void
  onComplete?: () => void
}

/** 把一个数值从 from 弹到 to；返回控制句柄，可随时 stop() */
export const springTo = (
  from: number,
  to: number,
  config: typeof DRAWER_SPRING | typeof CARD_SPRING,
  options: Options
): AnimationPlaybackControls =>
  animate(from, to, {
    ...config,
    velocity: options.velocity ?? 0,
    onUpdate: options.onUpdate,
    onComplete: options.onComplete,
  })
