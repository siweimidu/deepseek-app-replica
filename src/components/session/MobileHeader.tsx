import { IconMenuOutline20, IconNewChatOutline20 } from '../base/icons.js'
import { IconPhoneOutline20 } from '../base/appIcons.js'
import { openVoiceCall } from '../call/callState.js'
import { useTranslate } from '../../i18n/index.js'
import { android } from '../../app/android.js'
import { newChat } from '../../services/chat/store.js'
import { setAutoRead, useSettings } from '../../services/settings.js'
import { stopReadAloud } from '../../services/speech/readAloud.js'
import { AndroidSound } from '../base/AndroidIcons.js'
import { IconButton } from '../base/IconButton.js'
import { showToast } from '../base/toastState.js'
import { openMobileSider } from '../sider/mobileSiderState.js'
import styles from './MobileHeader.module.css'

/** 移动端顶栏：左侧菜单打开侧边栏；会话页再显示标题与开启新对话 */
export const MobileHeader = ({ title }: { title?: string }) => {
  const t = useTranslate()
  const autoRead = useSettings((state) => state.autoRead)
  return (
    <div className={styles.header}>
      <IconButton
        size="xl"
        tone="primary"
        className={styles.menu}
        icon={<IconMenuOutline20 />}
        aria-label={t('expandSiderbarButton')}
        onClick={openMobileSider}
      />
      {title === undefined && !android ? null : (
        <>
          <div className={styles.title}>{title}</div>
          {android ? (
            <IconButton
              size="xl"
              tone="primary"
              className={styles.call}
              icon={<IconPhoneOutline20 />}
              aria-label={t('callStart')}
              onClick={() => {
                stopReadAloud()
                openVoiceCall()
              }}
            />
          ) : null}
          {android ? (
            <IconButton
              size="xl"
              tone="primary"
              className={styles.sound}
              icon={<AndroidSound muted={!autoRead} />}
              aria-label={t('androidAutoRead')}
              aria-pressed={autoRead}
              onClick={() => {
                setAutoRead(!autoRead)
                if (autoRead) {
                  stopReadAloud()
                }
                showToast({ key: autoRead ? 'androidAutoReadDisabled' : 'androidAutoReadEnabled' })
              }}
            />
          ) : null}
          <IconButton
            size="xl"
            tone="primary"
            className={styles.newChat}
            icon={<IconNewChatOutline20 />}
            aria-label={t('newChat')}
            onClick={newChat}
          />
        </>
      )}
    </div>
  )
}
