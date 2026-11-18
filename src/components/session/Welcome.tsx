import { useIsMobile } from '../../app/viewport.js'
import { android } from '../../app/android.js'
import appIcon from '../../assets/deepsleep-avatar.jpg'
import { useTranslate, type TranslationKey } from '../../i18n/index.js'
import { ChatInput } from '../chatInput/ChatInput.js'
import { MobileHeader } from './MobileHeader.js'
import styles from './Welcome.module.css'

/** 官方按当前时段问候：早上 / 中午 / 下午 / 晚上 */
const greetingKey = (): TranslationKey => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 11) {
    return 'androidGreetingMorning'
  }
  if (hour >= 11 && hour < 13) {
    return 'androidGreetingNoon'
  }
  if (hour >= 13 && hour < 18) {
    return 'androidGreetingAfternoon'
  }
  return 'androidGreetingEvening'
}

/** 新对话：问候语 + 输入框。桌面端居中；移动端输入框吸底 */
export const Welcome = () => {
  const t = useTranslate()
  const isMobile = useIsMobile()
  return (
    <div className={styles.container}>
      {isMobile ? <MobileHeader /> : null}
      <div className={styles.welcome}>
        <div className={styles.greeting}>
          {android ? <img className={styles.appIcon} src={appIcon} alt="" /> : null}
          {t(android ? greetingKey() : 'welcomeMessageChat250808')}
        </div>
        <ChatInput sessionId={null} />
        {isMobile && !android ? <div className={styles.caveat}>{t('contentCaveat')}</div> : null}
      </div>
    </div>
  )
}
