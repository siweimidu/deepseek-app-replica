import { useEffect, useState } from 'react'
import { openSettings } from '../settings/settingsDialogState.js'
import { translate } from '../../i18n/index.js'
import { dismissImportJob, useImportJob } from '../../services/chat/importJob.js'
import { IconChevronRightOutline14 } from './icons.js'
import styles from './ImportStatusBar.module.css'

/**
 * 顶部导入状态条：任务存在模块 store 里，因此离开数据管理页后
 * 这一条仍然跟随用户在整个 App 内显示进度，点击回到数据管理页。
 */
export const ImportStatusBar = () => {
  const { phase, percent, sessions } = useImportJob()
  const [shown, setShown] = useState(false)
  const active = phase === 'downloading' || phase === 'reading' || phase === 'writing'

  useEffect(() => {
    if (!active) {
      return
    }
    const frame = requestAnimationFrame(() => setShown(true))
    return () => cancelAnimationFrame(frame)
  }, [active])

  // 导入完成不展示任何结果条：直接把任务收掉，只保留进行中的进度
  useEffect(() => {
    if (phase === 'done') {
      dismissImportJob()
    }
  }, [phase])

  if (phase === 'idle' || phase === 'error' || phase === 'done') {
    return null
  }
  const value = Math.round(percent * 100)
  const label =
    phase === 'downloading'
      ? translate('historyImportDownloading', { percent: value })
      : translate('historyImportProgress', { percent: value })

  return (
    <button
      className={styles.bar}
      data-phase={phase}
      data-shown={shown ? 'true' : undefined}
      type="button"
      onClick={() => openSettings('data')}
      aria-live="polite"
    >
      <span className={styles.dot} aria-hidden="true" />
      <span className={styles.label}>{label}</span>
      {sessions > 0 ? <span className={styles.count}>{sessions}</span> : null}
      <span className={styles.chevron} aria-hidden="true">
        <IconChevronRightOutline14 />
      </span>
      <span className={styles.track} aria-hidden="true">
        <span style={{ transform: `scaleX(${Math.min(1, Math.max(0.02, percent))})` }} />
      </span>
    </button>
  )
}
