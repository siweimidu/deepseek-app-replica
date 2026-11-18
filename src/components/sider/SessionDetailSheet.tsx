import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import clsx from 'clsx'
import { usePredictiveBack } from '../../app/backGesture.js'
import { useTranslate } from '../../i18n/index.js'
import { loadSession, useChatStore } from '../../services/chat/store.js'
import type { SessionSummary } from '../../services/chat/types.js'
import { MODEL_LABELS, MODEL_WINDOWS } from '../../services/chat/context/budget.js'
import { formatDateTime } from '../../utils/format.js'
import { copyText } from '../../utils/clipboard.js'
import { showToast } from '../base/toastState.js'
import {
  IconChatOutline20,
  IconClockOutline20,
  IconCopyOutline20,
  IconIdOutline20,
  IconInfoOutline20,
} from '../base/appIcons.js'
import styles from './SessionDetailSheet.module.css'

const formatTokens = (value: number) =>
  value >= 1000 ? `${Math.round(value / 100) / 10}K` : String(value)

/** 128000 → 128K，1000000 → 1M */
const formatWindow = (value: number) =>
  value >= 1_000_000 ? `${Math.round(value / 100_000) / 10}M` : `${Math.round(value / 1000)}K`

const Row = ({
  icon,
  label,
  value,
  action,
}: {
  icon: React.ReactNode
  label: string
  value: React.ReactNode
  action?: React.ReactNode
}) => (
  <div className={styles.row}>
    <span className={styles.rowIcon} aria-hidden="true">
      {icon}
    </span>
    <div className={styles.rowBody}>
      <span className={styles.rowLabel}>{label}</span>
      <span className={styles.rowValue}>{value}</span>
    </div>
    {action}
  </div>
)

/**
 * 会话详情：来源、创建时间（导入时取导出包里的原始时间）、最后更新、
 * 消息数与会话 ID。与官方一致不显示置顶状态。
 */
export const SessionDetailSheet = ({
  session,
  onClose,
}: {
  session: SessionSummary
  onClose: () => void
}) => {
  const t = useTranslate()
  const loaded = useChatStore((state) => state.sessionCache[session.id])
  // 导出包里的会话 ID 由 DeepSeek 生成（session- 前缀），本机新建的是纯 UUID。
  const imported = session.id.startsWith('session-')
  // 挂载后下一帧再切换，保证 transition 从收起状态开始播。
  const [shown, setShown] = useState(false)
  // 缓存命中率：命中的缓存 token 占本轮输入侧总量的比例（只在详情里展示）
  // 会话本身不存模型，取最后一条助手消息的模型；没有就按默认
  const activeModel =
    (() => {
      const messages = loaded?.messages ?? []
      for (let index = messages.length - 1; index >= 0; index -= 1) {
        const candidate = messages[index]
        if (candidate.role === 'assistant' && candidate.model) {
          return candidate.model
        }
      }
      return null
    })() ?? 'deepseek-flash'

  const cache = (() => {
    const usage = loaded?.contextUsage
    if (!usage) {
      return null
    }
    // 服务端完全没返回缓存字段时，不要谎报 0%
    if (usage.cacheReadTokens + usage.cacheWriteTokens === 0) {
      return { label: '—', detail: '服务端未返回缓存数据' }
    }
    const total = usage.inputTokens + usage.cacheReadTokens + usage.cacheWriteTokens
    if (total <= 0) {
      return null
    }
    return {
      label: `${Math.round((usage.cacheReadTokens / total) * 100)}%`,
      detail: `命中 ${formatTokens(usage.cacheReadTokens)} / 输入 ${formatTokens(total)}`,
    }
  })()
  const sheet = useRef<HTMLElement>(null)
  // 预测性返回：手势期间弹层跟着手指往下退
  usePredictiveBack(sheet, onClose)

  useEffect(() => {
    const frame = requestAnimationFrame(() => setShown(true))
    return () => cancelAnimationFrame(frame)
  }, [])

  useEffect(() => {
    void loadSession(session.id)
  }, [session.id])

  return createPortal(
    <div className={clsx(styles.overlay, shown && styles.overlayShown)} onClick={onClose} role="presentation">
      <section
        ref={sheet}
        className={clsx(styles.sheet, shown && styles.sheetShown)}
        role="dialog"
        aria-modal="true"
        aria-label={t('sessionDetailOption')}
        onClick={(event) => event.stopPropagation()}
      >
        <span className={styles.handle} aria-hidden="true" />
        <h2 className={styles.title}>{session.title || t('untitledChat')}</h2>
        <div className={styles.card}>
          <Row
            icon={<IconInfoOutline20 />}
            label={t('sessionDetailSource')}
            value={imported ? t('sessionDetailSourceImported') : t('sessionDetailSourceLocal')}
          />
          <Row
            icon={<IconClockOutline20 />}
            label={t('sessionDetailCreatedAt')}
            value={formatDateTime(session.createdAt)}
          />
          <Row
            icon={<IconClockOutline20 />}
            label={t('sessionDetailUpdatedAt')}
            value={formatDateTime(session.updatedAt)}
          />
          <Row
            icon={<IconChatOutline20 />}
            label={t('sessionDetailMessages')}
            value={loaded ? loaded.messages.length : '—'}
          />
          {activeModel ? (
            <Row
              icon={<IconInfoOutline20 />}
              label={t('sessionDetailModel')}
              value={MODEL_LABELS[activeModel] ?? activeModel}
            />
          ) : null}
          {cache ? (
            <Row
              icon={<IconCopyOutline20 />}
              label={t('sessionDetailCacheHit')}
              value={`${cache.label} · ${cache.detail}`}
            />
          ) : null}
          {loaded?.contextUsage ? (
            <Row
              icon={<IconInfoOutline20 />}
              label={t('sessionDetailContext')}
              value={[
                `${formatTokens(loaded.contextUsage.inputTokens)} / ${formatWindow(
                  MODEL_WINDOWS[activeModel] ?? MODEL_WINDOWS['deepseek-flash']
                )}`,
                loaded.anchor ? '已存档开头' : '',
              ]
                .filter(Boolean)
                .join(' · ')}
            />
          ) : null}
          <Row
            icon={<IconIdOutline20 />}
            label={t('sessionDetailId')}
            value={<span className={styles.mono}>{session.id}</span>}
            action={
              <button
                type="button"
                className={styles.copy}
                aria-label={t('sessionDetailId')}
                onClick={() => {
                  void copyText(session.id).then((ok) =>
                    showToast(ok ? { key: 'copied' } : { key: 'copyFailed', type: 'error' })
                  )
                }}
              >
                <IconCopyOutline20 />
              </button>
            }
          />
        </div>
      </section>
    </div>,
    document.body
  )
}
