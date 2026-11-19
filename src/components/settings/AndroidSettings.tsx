import { useEffect, useRef, useState, type ReactNode } from 'react'
import { android, saveAndroidHistory } from '../../app/android.js'
import { usePredictiveBack } from '../../app/backGesture.js'
import { useTranslate } from '../../i18n/index.js'
import type { TtsVoice } from '../../services/api/speech.js'
import { clearHistory, exportHistory } from '../../services/chat/backup.js'
import { startFileImport, startLinkImport, useImportJob } from '../../services/chat/importJob.js'
import { normalizeArchiveUrl } from '../../services/chat/history/linkImport.js'
import { checkAppUpdate, installAppUpdate, installedVersionCode, openInstallPermission, type UpdateInfo, type UpdateProgress } from '../../services/appUpdate.js'
import { useChatStore } from '../../services/chat/store.js'
import {
  setApiKey,
  setFoldThinking,
  setFontSize,
  setLocale,
  setThemePreference,
  setTtsVoice,
  useSettings,
  setAvatar,
  setAccountName,
  type LocalePreference,
  type ThemePreference,
} from '../../services/settings.js'
import { AndroidSound } from '../base/AndroidIcons.js'
import {
  IconChevronRightOutline14,
  IconCloseOutline16,
  IconDataOutline16,
  IconGlobeLanguageOutline14,
  IconLightOutline16,
  IconLinkOutline16,
  IconSettingsOutline16,
} from '../base/icons.js'
import { showToast } from '../base/toastState.js'
import { ApiKeyConfirm, ApiKeyField, useApiKeyEditor } from './ApiKeyField.js'
import { closeSettings, useSettingsDialog } from './settingsDialogState.js'
import defaultAvatar from '../../assets/deepsleep-avatar.jpg'
import { AvatarEditor } from './AvatarEditor.js'
import styles from './AndroidSettings.module.css'

type Page =
  | 'root'
  | 'account'
  | 'data'
  | 'export'
  | 'font'
  | 'personalization'
  | 'agreements'
  | 'help'
type Popup = 'locale' | 'theme' | 'voice' | 'logout' | 'delete' | 'link' | 'avatar' | 'name' | 'update'

const Profile = () => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
  >
    <circle cx="12" cy="8" r="4" />
    <path d="M4.5 21a7.5 6 0 0 1 15 0" />
  </svg>
)

const Info = ({ glyph = 'i' }: { glyph?: string }) => <span className={styles.info}>{glyph}</span>

const Group = ({
  label,
  children,
  spaced,
}: {
  label?: string
  children: ReactNode
  spaced?: boolean
}) => (
  <section className={styles.group} data-spaced={spaced ? '' : undefined}>
    {label ? <h2>{label}</h2> : null}
    <div className={styles.card}>{children}</div>
  </section>
)

const Row = ({
  label,
  icon,
  value,
  onClick,
  href,
  control,
  danger = false,
  disabled = false,
  arrow = Boolean(onClick || href),
}: {
  label: string
  icon?: ReactNode
  value?: string
  onClick?: () => void
  href?: string
  control?: ReactNode
  danger?: boolean
  disabled?: boolean
  arrow?: boolean
}) => {
  const contents = (
    <>
      {icon ? <span className={styles.icon}>{icon}</span> : null}
      <span className={styles.rowLabel}>{label}</span>
      {value ? <span className={styles.value}>{value}</span> : null}
      {control}
      {arrow ? (
        <span className={styles.arrow}>
          <IconChevronRightOutline14 />
        </span>
      ) : null}
    </>
  )
  if (href) {
    return (
      <a className={styles.row} href={href}>
        {contents}
      </a>
    )
  }
  if (onClick) {
    return (
      <button
        type="button"
        className={styles.row}
        data-danger={danger}
        disabled={disabled}
        onClick={onClick}
      >
        {contents}
      </button>
    )
  }
  return <div className={styles.row}>{contents}</div>
}

const Switch = ({
  label,
  checked,
  toggle,
}: {
  label: string
  checked: boolean
  toggle?: () => void
}) => (
  <button
    type="button"
    className={styles.switch}
    role="switch"
    aria-label={label}
    aria-checked={checked}
    disabled={!toggle}
    onClick={toggle}
  >
    <span />
  </button>
)

const Choice = <T extends string>({
  title,
  icon,
  value,
  fields,
  confirm,
  dismiss,
}: {
  title: string
  icon?: ReactNode
  value: T
  fields: ReadonlyArray<{ id: T; label: string }>
  confirm: (value: T) => void
  dismiss: () => void
}) => {
  const t = useTranslate()
  const [next, setNext] = useState(value)
  return (
    <div
      className={styles.overlay}
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          dismiss()
        }
      }}
    >
      <section className={styles.choice} role="dialog" aria-modal="true" aria-label={title}>
        <header>
          {icon}
          {title}
        </header>
        <div className={styles.options} role="radiogroup" aria-label={title}>
          {fields.map((field) => (
            <button
              key={field.id}
              type="button"
              role="radio"
              aria-checked={next === field.id}
              onClick={() => setNext(field.id)}
            >
              {field.label}
            </button>
          ))}
        </div>
        <button type="button" className={styles.confirm} onClick={() => confirm(next)}>
          {t('confirm')}
        </button>
      </section>
    </div>
  )
}

export const AndroidSettings = () => {
  const open = useSettingsDialog((state) => state.open)
  const section = useSettingsDialog((state) => state.section)
  return open ? <Settings start={section === 'data' ? 'account' : 'root'} key={section} /> : null
}

const Settings = ({ start }: { start: Page }) => {
  const t = useTranslate()
  const {
    locale,
    localePreference,
    themePreference,
    fontSize,
    foldThinking,
    ttsVoice,
    avatar,
    accountName,
  } = useSettings()
  const tr = (chinese: string, english: string) => (locale === 'zh-CN' ? chinese : english)
  const [page, setPage] = useState<Page>(start)
  const [popup, setPopup] = useState<Popup | null>(null)
  const [tone, setTone] = useState(ttsVoice)
  const [busy, setBusy] = useState(false)
  const [link, setLink] = useState('')
  const [archive, setArchive] = useState<Awaited<ReturnType<typeof exportHistory>> | null>(null)
  const importInput = useRef<HTMLInputElement>(null)
  const linkInput = useRef<HTMLTextAreaElement>(null)
  const avatarInput = useRef<HTMLInputElement>(null)
  const [avatarFile, setAvatarFile] = useState<File | null>(null)
  const [nameDraft, setNameDraft] = useState('')
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null)
  const [updateProgress, setUpdateProgress] = useState<UpdateProgress | null>(null)
  const [updateBusy, setUpdateBusy] = useState(false)
  const sessions = useChatStore((state) => state.sessions.length)
  const editor = useApiKeyEditor()
  const job = useImportJob()
  const percent = Math.round(job.percent * 100)
  const importing =
    job.phase === 'downloading' || job.phase === 'reading' || job.phase === 'writing'

  const labels: Record<Page, string> = {
    root: t('settings'),
    account: tr('账号管理', 'Account management'),
    data: tr('数据管理', 'Data management'),
    export: t('exportAllLabel'),
    font: tr('字体大小', 'Text size'),
    personalization: tr('个性化', 'Personalization'),
    agreements: tr('服务协议', 'Terms and policies'),
    help: tr('帮助与反馈', 'Help and feedback'),
  }
  const language = tr('语言', 'Language')
  const appearance = tr('外观', 'Appearance')
  const voice = tr('朗读音色', 'Read-aloud voice')
  const autoFold = tr('思考内容自动折叠', 'Collapse thinking automatically')
  const follow = tr('跟随系统', 'Follow system')
  const logout = tr('退出登录', 'Sign out')
  const clear = tr('删除所有历史对话', 'Delete all conversations')
  const themes: { id: ThemePreference; label: string }[] = [
    { id: 'system', label: tr('系统', 'System') },
    { id: 'light', label: tr('浅色', 'Light') },
    { id: 'dark', label: tr('深色', 'Dark') },
  ]
  const languages: { id: LocalePreference; label: string }[] = [
    { id: 'system', label: tr('系统', 'System') },
    { id: 'zh-CN', label: '中文（简体中文）' },
    { id: 'en-US', label: 'English' },
  ]
  const tones: { id: TtsVoice; label: string; description: string }[] = [
    {
      id: 'stella',
      label: t('settingsTtsVoiceStella'),
      description: tr('清晰明亮', 'Clear and bright'),
    },
    {
      id: 'tide',
      label: t('settingsTtsVoiceTide'),
      description: tr('沉稳自然', 'Calm and natural'),
    },
  ]
  const currentTone = tones.find((item) => item.id === tone) ?? tones[0]
  const languageLabel = languages.find((item) => item.id === locale)?.label
  const themeLabel = themes.find((item) => item.id === themePreference)?.label
  const policyBase = 'https://cdn.deepseek.com/policies/zh-CN/'

  const back = () => {
    if (busy) {
      return
    }
    if (popup) {
      setPopup(null)
      setLink('')
    } else if (page === 'root') {
      closeSettings()
    } else {
      setPage(page === 'export' ? 'data' : 'root')
    }
  }

  useEffect(() => {
    const onBack = (event: Event) => {
      event.preventDefault()
      back()
    }
    window.addEventListener('android-back', onBack)
    return () => window.removeEventListener('android-back', onBack)
  })

  // 预测性返回：手势期间整页跟随位移，松手完成后再真正回退
  const pageRef = useRef<HTMLElement>(null)
  usePredictiveBack(pageRef, back)

  const runExportAction = async (action: () => Promise<void>) => {
    setBusy(true)
    try {
      await action()
    } catch (error) {
      showToast({
        key: 'historyExportFailed',
        params: { message: error instanceof Error ? error.message : String(error) },
        type: 'error',
      })
    } finally {
      setBusy(false)
    }
  }

  const confirmAction = async () => {
    if (busy) {
      return
    }
    if (popup === 'logout') {
      if (setApiKey(null)) {
        closeSettings()
      } else {
        showToast({ key: 'apiKeyStorageFailed' })
      }
      return
    }
    setBusy(true)
    try {
      if (popup === 'delete') {
        await clearHistory()
        showToast({ key: 'historyDeleted' })
        setPopup(null)
      }
    } catch {
      showToast({ key: 'historyDeleteFailed', type: 'error' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section
      ref={pageRef}
      className={styles.page}
      role="region"
      aria-label={labels[page]}
    >
      <header className={styles.header}>
        <button
          type="button"
          className={styles.back}
          aria-label={tr('返回', 'Back')}
          onClick={back}
        >
          <IconChevronRightOutline14 />
        </button>
        <h1>{labels[page]}</h1>
      </header>
      <div className={styles.scroll} key={page}>
        {page === 'root' ? (
          <>
            <Group label={tr('账户', 'Account')}>
              <Row label={labels.account} icon={<Profile />} onClick={() => setPage('account')} />
              <Row
                label={labels.data}
                icon={<IconDataOutline16 />}
                onClick={() => setPage('data')}
              />
            </Group>
            <Group label={tr('应用', 'App')}>
              <Row
                label={language}
                value={languageLabel}
                icon={<IconGlobeLanguageOutline14 />}
                onClick={() => setPopup('locale')}
              />
              <Row
                label={appearance}
                value={themeLabel}
                icon={<IconLightOutline16 />}
                onClick={() => setPopup('theme')}
              />
              <Row
                label={labels.font}
                icon={<span className={styles.fontIcon}>ᴀA</span>}
                onClick={() => setPage('font')}
              />
              <Row
                label={labels.personalization}
                icon={<IconSettingsOutline16 />}
                onClick={() => setPage('personalization')}
              />
            </Group>
            <Group label={tr('语音', 'Voice')}>
              <Row
                label={voice}
                icon={<AndroidSound muted={false} />}
                arrow={false}
                onClick={() => {
                  setTone(ttsVoice)
                  setPopup('voice')
                }}
              />
            </Group>
            <Group label={tr('关于', 'About')}>
              <Row
                label={labels.agreements}
                icon={<IconLinkOutline16 />}
                onClick={() => setPage('agreements')}
              />
            </Group>
            <Group spaced>
              <Row
                label={tr('检查更新', 'Check for updates')}
                value={`build${installedVersionCode()}`}
                icon={<IconSettingsOutline16 />}
                onClick={async () => {
                  try {
                    const info = await checkAppUpdate()
                    if (!info.available) {
                      showToast(tr('已是最新版本', 'You are up to date'))
                      return
                    }
                    setUpdateInfo(info)
                    setUpdateProgress(null)
                    setPopup('update')
                  } catch (error) {
                    showToast({
                      key: 'historyImportFailedDetail',
                      params: { message: error instanceof Error ? error.message : String(error) },
                      type: 'error',
                    })
                  }
                }}
              />
            </Group>
            <Group spaced>
              <Row label={labels.help} icon={<Info glyph="?" />} onClick={() => setPage('help')} />
            </Group>
            <Group spaced>
              <Row label={logout} danger arrow={false} onClick={() => setPopup('logout')} />
            </Group>
          </>
        ) : null}
        {page === 'account' ? (
          <>
            <Group label={tr('账户', 'Account')}>
              <button
                type="button"
                className={styles.avatarRow}
                onClick={() => avatarInput.current?.click()}
              >
                <span className={styles.avatarPreview}>
                  <img src={avatar ?? defaultAvatar} alt="" />
                </span>
                <span className={styles.avatarText}>
                  <span className={styles.avatarName}>{tr('头像', 'Photo')}</span>
                  <span className={styles.avatarHint}>{t('accountAvatarChange')}</span>
                </span>
                <span className={styles.arrow}>
                  <IconChevronRightOutline14 />
                </span>
              </button>
              <input
                ref={avatarInput}
                hidden
                type="file"
                accept="image/*"
                onChange={(event) => {
                  const picked = event.target.files?.[0]
                  event.target.value = ''
                  if (picked) {
                    setAvatarFile(picked)
                  }
                }}
              />
              <Row
                label={tr('账户名称', 'Account name')}
                value={accountName || 'API Key'}
                onClick={() => {
                  setNameDraft(accountName ?? '')
                  setPopup('name')
                }}
              />
              <Row
                label="DeepSeek API Key"
                value="••••••••"
                onClick={() => editor.setEditing(true)}
              />
              {editor.editing ? (
                <div className={styles.credentials}>
                  <ApiKeyField editor={editor} />
                  <ApiKeyConfirm editor={editor} />
                </div>
              ) : null}
              <Row
                label={tr('开放平台', 'Open platform')}
                href="https://platform.deepseek.com/api_keys"
              />
            </Group>
          </>
        ) : null}
        {page === 'data' ? (
          <>
            <p className={styles.caption}>
              {tr(
                '历史对话保存在此设备。API 数据处理适用 DeepSeek 开放平台隐私政策。',
                'Chat history is stored on this device. API usage is subject to the DeepSeek Open Platform Privacy Policy.'
              )}
            </p>
            <Group>
              <Row label={labels.export} disabled={busy} onClick={() => setPage('export')} />
            </Group>
            <Group>
              <Row
                label={clear}
                danger
                arrow={false}
                disabled={busy}
                onClick={() => setPopup('delete')}
              />
            </Group>
            <Group>
              <Row
                label={t('historyPickFile')}
                icon={<IconDataOutline16 />}
                arrow={false}
                disabled={busy || importing}
                onClick={() => importInput.current?.click()}
              />
              <input
                ref={importInput}
                hidden
                type="file"
                accept=".zip,application/zip"
                onChange={(event) => {
                  const selected = event.target.files?.[0]
                  event.target.value = ''
                  if (selected) {
                    startFileImport(selected)
                  }
                }}
              />
              <Row
                label={t('historyImportFromLink')}
                icon={<IconLinkOutline16 />}
                arrow={false}
                disabled={busy || importing}
                onClick={() => setPopup('link')}
              />
            </Group>
            {importing || job.phase === 'done' || job.phase === 'error' ? (
              <Group label={t('historyImportProgressTitle')}>
                <div className={styles.importState} data-tone={job.phase}>
                  <div className={styles.importHead}>
                    <span className={styles.importTitle}>
                      {job.phase === 'downloading'
                        ? t('historyImportDownloading', { percent })
                        : job.phase === 'error'
                          ? t('historyImportFailed')
                          : job.phase === 'done'
                            ? t('historyImported', {
                                count: (job.finished?.added ?? 0) + (job.finished?.updated ?? 0),
                              })
                            : t('historyImportProgress', { percent })}
                    </span>
                    <span className={styles.importPercent}>{percent}%</span>
                  </div>
                  <div className={styles.importTrack} aria-hidden="true">
                    <span
                      style={{
                        transform: `scaleX(${Math.min(1, Math.max(0.02, job.percent))})`,
                      }}
                    />
                  </div>
                  <p className={styles.importNote}>
                    {job.phase === 'error'
                      ? job.failure
                      : job.phase === 'done' && job.finished
                        ? t('historyImportSummary', {
                            added: job.finished.added,
                            updated: job.finished.updated,
                          })
                        : t('historyImportBackground')}
                  </p>
                </div>
              </Group>
            ) : null}
          </>
        ) : null}
        {page === 'export' ? (
          <>
            <Group>
              <Row
                label={archive ? tr('重新导出', 'Export again') : tr('导出', 'Export')}
                arrow={false}
                disabled={busy || !sessions}
                onClick={() =>
                  void runExportAction(async () => {
                    setArchive(await exportHistory())
                  })
                }
              />
            </Group>
            {archive ? (
              <Group>
                <Row
                  label={tr('保存到设备', 'Save to device')}
                  arrow={false}
                  disabled={busy}
                  onClick={() =>
                    void runExportAction(() => saveAndroidHistory(archive.name, archive.blob))
                  }
                />
              </Group>
            ) : null}
            <p className={styles.caption} role="status">
              {busy
                ? tr('正在处理归档…', 'Working on the archive…')
                : (archive?.name ?? t(sessions ? 'historyExportDescription' : 'androidNoChats'))}
            </p>
          </>
        ) : null}
        {page === 'font' ? (
          <div
            className={styles.preview}
            style={{
              fontSize: `${16 * (fontSize === null ? (android?.systemFontScale() ?? 1) : 1 + (fontSize - 3) * 0.09)}px`,
            }}
          >
            <span>{tr('预览文字大小', 'Preview text size')}</span>
            <p>
              {tr('你可以拖动滑块来调整字体大小。', 'Drag the slider to adjust the text size.')}
            </p>
            <p>
              {tr(
                '如果在使用过程中存在问题或建议，可反馈给 DeepSeek 团队。',
                'You can share questions or suggestions with DeepSeek.'
              )}
            </p>
          </div>
        ) : null}
        {page === 'personalization' ? (
          <>
            <Group>
              <Row
                label={autoFold}
                control={
                  <Switch
                    label={autoFold}
                    checked={foldThinking}
                    toggle={() => setFoldThinking(!foldThinking)}
                  />
                }
              />
            </Group>
            <p className={styles.caption}>
              {tr(
                '开启后，思考结束后将自动折叠思考内容',
                'Collapse thinking once an answer is ready.'
              )}
            </p>
          </>
        ) : null}
        {page === 'agreements' ? (
          <Group>
            <Row
              label={tr('用户协议', 'Terms of use')}
              href={policyBase + 'deepseek-terms-of-use.html'}
            />
            <Row
              label={tr('隐私政策', 'Privacy policy')}
              href={policyBase + 'deepseek-open-platform-privacy-policy.html'}
            />
            <Row
              label={tr('个人信息收集清单', 'Personal information collected')}
              href={policyBase + 'collected-personal-information.html'}
            />
            <Row
              label={tr('应用权限', 'App permissions')}
              onClick={() => android?.openAppPermissions()}
            />
          </Group>
        ) : null}
        {page === 'help' ? (
          <Group>
            <Row
              label={tr('开放平台帮助', 'API help')}
              href="https://api-docs.deepseek.com/zh-cn/"
            />
          </Group>
        ) : null}
      </div>
      {page === 'font' ? (
        <div className={styles.fontPanel}>
          <Row
            label={follow}
            control={
              <Switch
                label={follow}
                checked={fontSize === null}
                toggle={() => setFontSize(fontSize === null ? 3 : null)}
              />
            }
          />
          <div className={styles.fontLabels}>
            <small>A</small>
            <span>{tr('标准', 'Standard')}</span>
            <strong>A</strong>
          </div>
          <input
            type="range"
            aria-label={labels.font}
            min="0"
            max="6"
            step="1"
            value={fontSize ?? 3}
            disabled={fontSize === null}
            onChange={(event) => setFontSize(event.target.valueAsNumber)}
          />
        </div>
      ) : null}
      {popup === 'locale' ? (
        <Choice
          title={language}
          icon={<IconGlobeLanguageOutline14 />}
          value={localePreference}
          fields={languages}
          confirm={(value) => {
            setLocale(value)
            setPopup(null)
          }}
          dismiss={back}
        />
      ) : null}
      {popup === 'theme' ? (
        <Choice
          title={appearance}
          value={themePreference}
          fields={themes}
          confirm={(value) => {
            setThemePreference(value)
            setPopup(null)
          }}
          dismiss={back}
        />
      ) : null}
      {popup === 'voice' ? (
        <div className={styles.overlay} data-sheet="">
          <section className={styles.voiceSheet} role="dialog" aria-modal="true" aria-label={voice}>
            <header>
              {voice}
              <button type="button" aria-label={t('close')} onClick={back}>
                <IconCloseOutline16 />
              </button>
            </header>
            <div
              className={styles.voiceBody}
              onTouchStart={(event) => {
                event.currentTarget.dataset.swipeX = String(event.touches[0].clientX)
              }}
              onTouchEnd={(event) => {
                const dx =
                  event.changedTouches[0].clientX - Number(event.currentTarget.dataset.swipeX)
                if (Math.abs(dx) > 32) {
                  setTone(dx > 0 ? 'stella' : 'tide')
                }
              }}
            >
              <div className={styles.voiceArt} data-tone={tone} aria-hidden="true" />
              <div>{currentTone.label}</div>
              <small>{currentTone.description}</small>
              <div className={styles.dots} role="radiogroup" aria-label={voice}>
                {tones.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    role="radio"
                    aria-label={item.label}
                    aria-checked={tone === item.id}
                    onClick={() => setTone(item.id)}
                  />
                ))}
              </div>
            </div>
            <button
              className={styles.primary}
              type="button"
              onClick={() => {
                setTtsVoice(tone)
                setPopup(null)
              }}
            >
              {t('confirm')}
            </button>
          </section>
        </div>
      ) : null}
      {popup === 'logout' || popup === 'delete' ? (
        <div className={styles.overlay}>
          <section className={styles.choice} role="dialog" aria-modal="true">
            <header>{popup === 'logout' ? logout : clear}</header>
            <p className={styles.message}>
              {popup === 'logout'
                ? tr('确认退出当前 API Key？', 'Sign out of this API Key?')
                : t('deleteAllSessionsModalDescription')}
            </p>
            <div className={styles.confirmActions}>
              <button className={styles.confirm} disabled={busy} onClick={back}>
                {t('cancel')}
              </button>
              <button
                className={styles.confirm}
                disabled={busy}
                data-danger=""
                onClick={() => void confirmAction()}
              >
                {t('confirm')}
              </button>
            </div>
          </section>
        </div>
      ) : null}
      {popup === 'update' && updateInfo ? (
        <div className={styles.nameOverlay} role="presentation" onClick={() => setPopup(null)}>
          <section
            className={styles.nameCard}
            role="dialog"
            aria-modal="true"
            aria-label={tr('发现新版本', 'Update available')}
            onClick={(event) => event.stopPropagation()}
          >
            <h2 className={styles.nameTitle}>
              {tr('发现新版本', 'Update available')} {updateInfo.tag}
            </h2>
            <p className={styles.nameHint}>
              {tr('当前 build', 'Current build')}
              {updateInfo.current}
              {' → build'}
              {updateInfo.latest}
              {updateInfo.size > 0 ? ` · ${(updateInfo.size / 1024 / 1024).toFixed(1)} MB` : ''}
            </p>
            {updateInfo.notes ? (
              <p className={styles.updateNotes}>{updateInfo.notes.slice(0, 400)}</p>
            ) : null}
            {updateProgress && updateProgress.state !== 'ready' ? (
              <p className={styles.updateProgress}>
                {updateProgress.state === 'error'
                  ? updateProgress.message
                  : `${tr('正在下载', 'Downloading')} ${Math.max(0, updateProgress.percent)}%`}
              </p>
            ) : null}
            <div className={styles.nameActions}>
              <button type="button" className={styles.nameCancel} onClick={() => setPopup(null)}>
                {t('cancel')}
              </button>
              <button
                type="button"
                className={styles.nameSave}
                disabled={updateBusy}
                onClick={async () => {
                  setUpdateBusy(true)
                  setUpdateProgress({ state: 'downloading', percent: 0, loaded: 0, total: updateInfo.size, message: '' })
                  try {
                    await installAppUpdate(updateInfo.url, setUpdateProgress)
                    showToast(tr('已开始安装，按提示完成即可', 'Installer opened'))
                    setPopup(null)
                  } catch (error) {
                    const message = error instanceof Error ? error.message : String(error)
                    setUpdateProgress({ state: 'error', percent: 0, loaded: 0, total: 0, message })
                    if (/install|安装|permission|Permission/.test(message)) {
                      openInstallPermission()
                    }
                  } finally {
                    setUpdateBusy(false)
                  }
                }}
              >
                {updateBusy ? tr('处理中…', 'Working…') : tr('下载并安装', 'Download and install')}
              </button>
            </div>
          </section>
        </div>
      ) : null}
      {popup === 'name' ? (
        <div
          className={styles.nameOverlay}
          role="presentation"
          onClick={() => setPopup(null)}
        >
          <section
            className={styles.nameCard}
            role="dialog"
            aria-modal="true"
            aria-label={tr('账户名称', 'Account name')}
            onClick={(event) => event.stopPropagation()}
          >
            <h2 className={styles.nameTitle}>{tr('账户名称', 'Account name')}</h2>
            <p className={styles.nameHint}>
              {tr(
                '只显示在侧边栏底部，不影响账号本身',
                'Shown at the bottom of the sidebar only'
              )}
            </p>
            <label className={styles.nameField}>
              <input
                autoFocus
                value={nameDraft}
                maxLength={20}
                spellCheck={false}
                autoCapitalize="off"
                autoComplete="off"
                enterKeyHint="done"
                placeholder="API Key"
                onChange={(event) => setNameDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    setAccountName(nameDraft)
                    setPopup(null)
                  }
                }}
              />
            </label>
            {accountName ? (
              <button
                type="button"
                className={styles.nameReset}
                onClick={() => {
                  setAccountName(null)
                  setPopup(null)
                }}
              >
                {tr('恢复默认（API Key）', 'Reset to API Key')}
              </button>
            ) : null}
            <div className={styles.nameActions}>
              <button type="button" className={styles.nameCancel} onClick={() => setPopup(null)}>
                {t('cancel')}
              </button>
              <button
                type="button"
                className={styles.nameSave}
                onClick={() => {
                  setAccountName(nameDraft)
                  setPopup(null)
                }}
              >
                {tr('保存', 'Save')}
              </button>
            </div>
          </section>
        </div>
      ) : null}
      {popup === 'link' ? (
        <div className={styles.overlay}>
          <section className={styles.choice} role="dialog" aria-modal="true">
            <header>{t('historyImportFromLink')}</header>
            <p className={styles.message}>{t('historyImportLinkHint')}</p>
            <label className={styles.linkField}>
              <span>{t('historyImportLinkLabel')}</span>
              <textarea
                ref={linkInput}
                value={link}
                rows={3}
                spellCheck={false}
                autoCapitalize="off"
                autoCorrect="off"
                placeholder={t('historyImportLinkPlaceholder')}
                onChange={(event) => setLink(event.target.value)}
              />
            </label>
            <div className={styles.confirmActions}>
              <button className={styles.confirm} onClick={back}>
                {t('cancel')}
              </button>
              <button
                className={styles.confirm}
                onClick={() => {
                  const value = (linkInput.current?.value ?? link).trim()
                  if (!value) {
                    showToast({ key: 'historyImportLinkEmpty', type: 'error' })
                    return
                  }
                  try {
                    const target = normalizeArchiveUrl(value)
                    setPopup(null)
                    setLink('')
                    startLinkImport(target)
                  } catch {
                    showToast({ key: 'historyImportLinkInvalid', type: 'error' })
                  }
                }}
              >
                {t('historyImportConfirm')}
              </button>
            </div>
          </section>
        </div>
      ) : null}
      {avatarFile ? (
        <AvatarEditor
          file={avatarFile}
          onCancel={() => setAvatarFile(null)}
          onDone={(dataUrl) => {
            setAvatar(dataUrl)
            setAvatarFile(null)
          }}
        />
      ) : null}
    </section>
  )
}
