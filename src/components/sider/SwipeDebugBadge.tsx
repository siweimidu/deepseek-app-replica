import { toggleSwipeDebug, useSwipeDebug } from './useDrawerSwipe.js'
import styles from './SwipeDebugBadge.module.css'

/** 手势调试角标：标题连点 5 次开关。出问题时能看出断在哪一环。 */
export const SwipeDebugBadge = () => {
  const { visible, down, move, toggle, last } = useSwipeDebug()
  if (!visible) {
    return null
  }
  return (
    <button type="button" className={styles.badge} onClick={toggleSwipeDebug}>
      down {down} · move {move} · toggle {toggle} · {last || '—'}
    </button>
  )
}
