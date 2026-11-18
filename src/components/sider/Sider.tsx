import clsx from 'clsx'
import { useEffect, useMemo, useRef, useState } from 'react'
import { android } from '../../app/android.js'
import { usePredictiveBack } from '../../app/backGesture.js'
import { useTranslate } from '../../i18n/index.js'
import {
  IconCloseOutline16,
  IconEllipsisOutline16,
  IconPanelLeftOutline16,
  IconSearchOutline16,
  IconSettingsOutline16,
  IconTrashOutline16,
  NewChatIcon,
} from '../base/icons.js'
import { IconPinOutline20 } from '../base/appIcons.js'
import { setPinnedSessions, setSiderCollapsed, useSettings } from '../../services/settings.js'
import { groupSessions } from '../../services/chat/sessionGroups.js'
import { newChat, removeSession, useChatStore } from '../../services/chat/store.js'
import type { SessionSummary } from '../../services/chat/types.js'
import { Button } from '../base/Button.js'
import { IconButton } from '../base/IconButton.js'
import { Modal } from '../base/Modal.js'
import { showToast } from '../base/toastState.js'
import { openSettings } from '../settings/settingsDialogState.js'
import { closeMobileSider, useMobileSider } from './mobileSiderState.js'
import { SessionDetailSheet } from './SessionDetailSheet.js'
import { SessionItem } from './SessionItem.js'
import { useSessionSearch } from './useSessionSearch.js'
import styles from './Sider.module.css'

const PersonIcon = () => (
  <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <circle cx="12" cy="8" r="4.15" />
    <path d="M3 23a9 7 0 0 1 18 0z" />
  </svg>
)

/** 展开的侧边栏：名称与收起按钮、开启新对话、按时间分组的会话列表、底部设置；移动端放在抽屉里，收起按钮关闭抽屉 */
export const Sider = ({ mobile = false }: { mobile?: boolean }) => {
  const t = useTranslate()
  const sessions = useChatStore((state) => state.sessions)
  const activeId = useChatStore((state) => state.activeId)
  const pinnedIds = useSettings((state) => state.pinnedSessions)
  const avatar = useSettings((state) => state.avatar)
  const androidDrawer = Boolean(mobile && android)
  const [query, setQuery] = useState('')
  const matches = useSessionSearch(query, sessions)
  const [now, setNow] = useState(Date.now)
  const [selecting, setSelecting] = useState(false)
  const [checked, setChecked] = useState<Set<string>>(() => new Set())
  const [detail, setDetail] = useState<SessionSummary | null>(null)
  const [pinning, setPinning] = useState<{ ids: Set<string>; unpin: boolean } | null>(null)
  const unpin = checked.size > 0 && [...checked].every((id) => pinnedIds.includes(id))
  const groups = useMemo(() => {
    if (!androidDrawer || pinnedIds.length === 0) {
      return groupSessions(matches, now, t)
    }
    const pinned = matches.filter((session) => pinnedIds.includes(session.id))
    const rest = groupSessions(
      matches.filter((session) => !pinnedIds.includes(session.id)),
      now,
      t
    )
    return pinned.length
      ? [{ key: 'pinned', label: t('androidPinned'), sessions: pinned }, ...rest]
      : rest
  }, [androidDrawer, matches, now, pinnedIds, t])
  const [deleting, setDeleting] = useState<SessionSummary[]>([])
  const [deletePending, setDeletePending] = useState(false)
  const drawerOpen = useMobileSider((state) => state.open)
  const closeSelection = () => {
    setSelecting(false)
    setChecked(new Set())
    setPinning(null)
  }

  const togglePin = (id: string) => {
    const pinned = pinnedIds.includes(id)
    setPinnedSessions(pinned ? pinnedIds.filter((item) => item !== id) : [...pinnedIds, id])
    showToast({
      key: pinned ? 'androidUnpinnedChats' : 'androidPinnedChats',
      params: { count: 1 },
    })
  }

  useEffect(() => {
    if (!drawerOpen) {
      closeSelection()
    }
  }, [drawerOpen])

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>
    const refresh = () => {
      clearTimeout(timer)
      const time = Date.now()
      setNow(time)
      const midnight = new Date(time).setHours(24, 0, 0, 0)
      timer = setTimeout(refresh, midnight - time)
    }
    const onVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        refresh()
      }
    }
    refresh()
    document.addEventListener('visibilitychange', onVisibilityChange)
    window.addEventListener('focus', refresh)
    return () => {
      clearTimeout(timer)
      document.removeEventListener('visibilitychange', onVisibilityChange)
      window.removeEventListener('focus', refresh)
    }
  }, [])

  return (
    <div className={clsx(styles.sider, mobile && styles.mobile, androidDrawer && styles.drawerSider)}>
      {androidDrawer && selecting ? (
        <div className={styles.selectionHeader}>
          <span>
            {checked.size
              ? t('androidSelectedChats', { count: checked.size })
              : t('androidSelectChats')}
          </span>
          <button
            type="button"
            className={styles.closeCircle}
            aria-label={t('close')}
            onClick={closeSelection}
          >
            <IconCloseOutline16 />
          </button>
        </div>
      ) : androidDrawer ? (
        <label className={styles.search}>
          <IconSearchOutline16 />
          <input
            type="search"
            placeholder={t('androidSearchChats')}
            aria-label={t('androidSearchChats')}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
      ) : (
        <>
          <div className={styles.top}>
            <div className={styles.appName}>{t('appName')}</div>
            <IconButton
              size="m"
              icon={<IconPanelLeftOutline16 />}
              tooltip={t('collapseSiderbarButton')}
              tooltipPlacement="bottom"
              onClick={() => (mobile ? closeMobileSider() : setSiderCollapsed(true))}
            />
          </div>
          <button
            type="button"
            className={styles.newChat}
            onClick={() => {
              newChat()
              closeMobileSider()
            }}
          >
            <span className={styles.newChatIcon}>
              <NewChatIcon />
            </span>
            {t('newChat')}
          </button>
        </>
      )}
      <div className={styles.listWrap}>
        <div className={styles.list}>
          {groups.map((group) => (
            <div key={group.key} className={styles.section}>
              <div className={styles.sectionHeader}>{group.label}</div>
              {group.sessions.map((session) => (
                <SessionItem
                  key={session.id}
                  session={session}
                  active={session.id === activeId}
                  pinned={pinnedIds.includes(session.id)}
                  onPin={() => togglePin(session.id)}
                  onDetail={() => setDetail(session)}
                  onSelectMode={() => {
                    setSelecting(true)
                    setChecked(new Set([session.id]))
                  }}
                  onDelete={() => setDeleting([session])}
                  selection={
                    selecting
                      ? {
                          checked: checked.has(session.id),
                          toggle: () => {
                            setChecked((previous) => {
                              const next = new Set(previous)
                              if (next.has(session.id)) {
                                next.delete(session.id)
                              } else {
                                next.add(session.id)
                              }
                              return next
                            })
                          },
                        }
                      : undefined
                  }
                />
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className={styles.bottom}>
        {selecting ? (
          <div className={styles.selectionActions}>
            <button
              type="button"
              disabled={!checked.size}
              onClick={() => setPinning({ ids: checked, unpin })}
            >
              <IconPinOutline20 />
              {t(unpin ? 'androidUnpin' : 'androidPinned')}
            </button>
            <span className={styles.selectionDivider} aria-hidden="true" />
            <button
              type="button"
              disabled={!checked.size}
              onClick={() => setDeleting(sessions.filter((session) => checked.has(session.id)))}
            >
              <IconTrashOutline16 />
              {t('delete')}
            </button>
          </div>
        ) : (
          <button
            type="button"
            className={styles.settings}
            aria-label={t('settings')}
            onClick={() => openSettings(androidDrawer ? 'data' : 'general')}
          >
            <span className={styles.settingsIcon} data-avatar={androidDrawer ? '' : undefined}>
              {androidDrawer ? (
                avatar ? (
                  <img className={styles.avatarImage} src={avatar} alt="" />
                ) : (
                  <PersonIcon />
                )
              ) : (
                <IconSettingsOutline16 />
              )}
            </span>
            <span className={styles.settingsLabel}>
              {androidDrawer ? 'API Key' : t('settings')}
            </span>
            {androidDrawer ? <IconEllipsisOutline16 /> : null}
          </button>
        )}
      </div>
      {detail ? <SessionDetailSheet session={detail} onClose={() => setDetail(null)} /> : null}
      {pinning ? (
        <Modal
          title={t(pinning.unpin ? 'androidUnpinConfirm' : 'androidPinConfirm', {
            count: pinning.ids.size,
          })}
          onClose={() => setPinning(null)}
          footer={
            <>
              <Button variant="outlined" onClick={() => setPinning(null)}>
                {t(pinning.unpin ? 'androidKeepPinned' : 'cancel')}
              </Button>
              <Button
                onClick={() => {
                  const ids = sessions.filter((session) => pinning.ids.has(session.id))
                  setPinnedSessions(
                    pinning.unpin
                      ? pinnedIds.filter((id) => !pinning.ids.has(id))
                      : [...new Set([...pinnedIds, ...ids.map(({ id }) => id)])]
                  )
                  showToast({
                    key: pinning.unpin ? 'androidUnpinnedChats' : 'androidPinnedChats',
                    params: { count: ids.length },
                  })
                  closeSelection()
                }}
              >
                {t(pinning.unpin ? 'androidUnpin' : 'androidPinned')}
              </Button>
            </>
          }
        />
      ) : null}
      {deleting.length ? (
        <Modal
          title={t('deleteSessionModalContentTitle')}
          onClose={() => {
            if (!deletePending) {
              setDeleting([])
            }
          }}
          footer={
            <>
              <Button variant="outlined" disabled={deletePending} onClick={() => setDeleting([])}>
                {t('cancel')}
              </Button>
              <Button
                variant="danger"
                disabled={deletePending}
                onClick={async () => {
                  setDeletePending(true)
                  try {
                    const remaining: SessionSummary[] = []
                    const deleted = new Set<string>()
                    for (const session of deleting) {
                      if (await removeSession(session.id)) {
                        deleted.add(session.id)
                      } else {
                        remaining.push(session)
                      }
                    }
                    setDeleting(remaining)
                    if (deleted.size) {
                      setPinnedSessions(pinnedIds.filter((id) => !deleted.has(id)))
                    }
                    if (remaining.length) {
                      showToast({ key: 'sessionDeleteFailed', type: 'error' })
                    } else {
                      closeSelection()
                    }
                  } finally {
                    setDeletePending(false)
                  }
                }}
              >
                {t('delete')}
              </Button>
            </>
          }
        >
          {t('deleteSessionWithFilesDescription')}
        </Modal>
      ) : null}
    </div>
  )
}

/** 移动端抽屉：浮在页面上方，点空白区域关闭。 */
export const MobileSider = () => {
  const open = useMobileSider((state) => state.open)
  const drawer = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (drawer.current) {
      drawer.current.inert = !open
    }
  }, [open])
  // 预测性返回：手势期间抽屉跟着手指往左退
  usePredictiveBack(drawer, closeMobileSider, android && open)
  if (!android && !open) {
    return null
  }
  return (
    <>
      {open ? <div className={styles.drawerMask} onClick={closeMobileSider} /> : null}
      <div className={styles.drawer} ref={drawer} data-android-drawer={android ? '' : undefined}>
        <Sider mobile />
      </div>
    </>
  )
}
