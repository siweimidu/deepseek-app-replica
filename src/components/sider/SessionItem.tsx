import clsx from 'clsx'
import { memo, useRef, useState } from 'react'
import { android } from '../../app/android.js'
import { useTranslate } from '../../i18n/index.js'
import {
  IconInfoOutline20,
  IconListOutline20,
  IconPencilOutline20,
  IconPinOutline20,
  IconPinSlashOutline20,
  IconTrashOutline20,
} from '../base/appIcons.js'
import { IconEllipsisOutline16 } from '../base/icons.js'
import { renameSession, selectSession } from '../../services/chat/store.js'
import type { SessionSummary } from '../../services/chat/types.js'
import { IconButton } from '../base/IconButton.js'
import { Menu } from '../base/Menu.js'
import { closeMobileSider } from './mobileSiderState.js'
import styles from './SessionItem.module.css'

export const SessionItem = memo(function SessionItem({
  session,
  active,
  pinned,
  onDelete,
  onPin,
  onDetail,
  onSelectMode,
  selection,
}: {
  session: SessionSummary
  active: boolean
  pinned: boolean
  onDelete: () => void
  onPin: () => void
  onDetail: () => void
  onSelectMode: () => void
  selection?: { checked: boolean; toggle: () => void }
}) {
  const t = useTranslate()
  const [editing, setEditing] = useState(false)
  const actionsRef = useRef<HTMLDivElement>(null)
  const displayTitle = session.title || t('untitledChat')

  if (selection) {
    return (
      <button
        className={clsx(styles.select, selection.checked && styles.checked)}
        type="button"
        role="checkbox"
        aria-checked={selection.checked}
        onClick={selection.toggle}
      >
        <span className={styles.checkbox} aria-hidden="true">
          {selection.checked ? (
            <svg width="14" height="14" viewBox="0 0 14 14">
              <path
                d="m3 7.3 2.7 2.7L11 4.4"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          ) : null}
        </span>
        <div className={styles.title}>{displayTitle}</div>
      </button>
    )
  }

  if (editing) {
    const finish = (title: string) => {
      setEditing(false)
      if (title.trim() && title.trim() !== displayTitle) {
        renameSession(session.id, title.trim())
      }
    }
    return (
      <input
        className={styles.renameInput}
        defaultValue={displayTitle}
        autoFocus
        onFocus={(event) => event.target.select()}
        onBlur={(event) => finish(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && !event.nativeEvent.isComposing) {
            finish(event.currentTarget.value)
          } else if (event.key === 'Escape') {
            setEditing(false)
          }
        }}
      />
    )
  }

  return (
    <div
      className={clsx(styles.item, active && styles.active)}
      data-session-id={session.id}
      onContextMenu={(event) => {
        if (android) {
          event.preventDefault()
          actionsRef.current?.querySelector('button')?.click()
        }
      }}
      onClick={() => {
        selectSession(session.id)
        closeMobileSider()
      }}
    >
      <div className={styles.title}>{displayTitle}</div>
      <div ref={actionsRef} className={styles.action} onClick={(event) => event.stopPropagation()}>
        <Menu
          variant="roomy"
          align="end"
          alignOffset={8}
          options={[
            {
              key: 'rename',
              label: t('sessionItemMenuRenameOption'),
              icon: <IconPencilOutline20 />,
              onSelect: () => setEditing(true),
            },
            {
              key: 'detail',
              label: t('sessionDetailOption'),
              icon: <IconInfoOutline20 />,
              divider: true,
              onSelect: onDetail,
            },
            {
              key: 'pin',
              label: t(pinned ? 'androidUnpin' : 'androidPinned'),
              icon: pinned ? <IconPinSlashOutline20 /> : <IconPinOutline20 />,
              divider: true,
              onSelect: onPin,
            },
            {
              key: 'select',
              label: t('multiSelect'),
              icon: <IconListOutline20 />,
              divider: true,
              onSelect: onSelectMode,
            },
            {
              key: 'delete',
              label: t('delete'),
              icon: <IconTrashOutline20 />,
              danger: true,
              divider: true,
              onSelect: onDelete,
            },
          ]}
        >
          {({ toggle }) => (
            <IconButton icon={<IconEllipsisOutline16 />} aria-label={t('more')} onClick={toggle} />
          )}
        </Menu>
      </div>
    </div>
  )
})
