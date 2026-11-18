import { useEffect, useRef, useState } from 'react'
import clsx from 'clsx'
import { usePredictiveBack } from '../../app/backGesture.js'
import { useTranslate } from '../../i18n/index.js'
import { useSettings, setTtsVoice, setSearch } from '../../services/settings.js'
import { useChatStore } from '../../services/chat/store.js'
import { closeVoiceCall, useVoiceCall } from './callState.js'
import { useCallSession } from './useCallSession.js'
import { IconChevronDownOutline14, IconGlobeLanguageOutline14 } from '../base/icons.js'
import {
  IconPhoneOffOutline,
  IconSwitchOutline20,
} from '../base/appIcons.js'
import styles from './VoiceCallScreen.module.css'

const MicrophoneIcon = ({ muted }: { muted: boolean }) => (
  <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true">
    <path d="M12 3.4a3 3 0 0 1 3 3v5.2a3 3 0 0 1-6 0V6.4a3 3 0 0 1 3-3Z" fill="currentColor" />
    <path
      d="M6.4 10.8a5.6 5.6 0 0 0 11.2 0M12 16.4v3.2"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      strokeLinecap="round"
    />
    {muted ? (
      <path d="m4.5 3.5 15 15" stroke="#ff5a52" strokeWidth="2.2" strokeLinecap="round" />
    ) : null}
  </svg>
)

const formatDuration = (total: number) => {
  const minutes = Math.floor(total / 60)
  const seconds = total % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

/** 通话页里的「朗读音色 + 回答设置」底部弹层 */
const CallSettingsSheet = ({ onClose }: { onClose: () => void }) => {
  const t = useTranslate()
  const { ttsVoice, search } = useSettings()
  const tones = [
    { id: 'stella' as const, label: t('settingsTtsVoiceStella'), description: t('callVoiceSweet') },
    { id: 'tide' as const, label: t('settingsTtsVoiceTide'), description: t('callVoiceDeep') },
  ]
  const active = tones.findIndex((tone) => tone.id === ttsVoice)
  const [dragX, setDragX] = useState(0)
  const startX = useRef<number | null>(null)

  const switchTo = (step: number) => {
    const next = (Math.max(0, active) + step + tones.length) % tones.length
    setTtsVoice(tones[next].id)
  }

  return (
    <div className={styles.sheetBackdrop} onClick={onClose} role="presentation">
      <section className={styles.sheet} onClick={(event) => event.stopPropagation()}>
        <h2>{t('callVoiceTitle')}</h2>
        <div
          className={styles.voiceStage}
          role="presentation"
          style={{ transform: `translateX(${dragX * 0.4}px)` }}
          onPointerDown={(event) => {
            startX.current = event.clientX
            event.currentTarget.setPointerCapture(event.pointerId)
          }}
          onPointerMove={(event) => {
            if (startX.current === null) {
              return
            }
            setDragX(event.clientX - startX.current)
          }}
          onPointerUp={(event) => {
            const moved = startX.current === null ? 0 : event.clientX - startX.current
            startX.current = null
            setDragX(0)
            if (Math.abs(moved) > 32) {
              switchTo(moved < 0 ? 1 : -1)
            }
          }}
          onPointerCancel={() => {
            startX.current = null
            setDragX(0)
          }}
        >
          <div className={styles.voicePreview} data-voice={ttsVoice} aria-hidden="true" />
          <div className={styles.voiceName}>{tones[active]?.label}</div>
          <div className={styles.voiceDesc}>{tones[active]?.description}</div>
          <div className={styles.dots} role="radiogroup" aria-label={t('callVoiceTitle')}>
            {tones.map((tone, index) => (
              <button
                key={tone.id}
                type="button"
                role="radio"
                aria-checked={index === active}
                aria-label={tone.label}
                className={styles.dot}
                onClick={() => setTtsVoice(tone.id)}
              />
            ))}
          </div>
        </div>
        <h2 className={styles.sectionTitle}>{t('callAnswerSettings')}</h2>
        <button
          type="button"
          className={styles.toggleRow}
          aria-pressed={search}
          onClick={() => setSearch(!search)}
        >
          <span className={styles.toggleLabel}>
            <IconGlobeLanguageOutline14 />
            {t('searchModeLabel')}
          </span>
          <span className={styles.switch} data-on={search ? 'true' : undefined} aria-hidden="true" />
        </button>
        <button type="button" className={styles.confirm} onClick={onClose}>
          {t('confirm')}
        </button>
      </section>
    </div>
  )
}

/**
 * 语音通话整屏：官方是沉浸式深色界面——顶部会话名与计时、
 * 中间会呼吸的光球、底部麦克风/挂断/切文字三个圆钮。
 */
export const VoiceCallScreen = () => {
  const open = useVoiceCall((state) => state.open)
  const t = useTranslate()
  const title = useChatStore((state) => {
    const active = state.sessions.find((session) => session.id === state.activeId)
    return active?.title ?? ''
  })
  const [sheet, setSheet] = useState(false)
  const [mode, setMode] = useState<'voice' | 'text'>('voice')
  const { phase, level, seconds, toggleMute, interrupt, endCall } = useCallSession(open)
  const page = useRef<HTMLDivElement>(null)
  usePredictiveBack(page, closeVoiceCall, open)

  useEffect(() => {
    if (!open) {
      setSheet(false)
      setMode('voice')
      return
    }
    const onBack = (event: Event) => {
      event.preventDefault()
      closeVoiceCall()
    }
    window.addEventListener('android-back', onBack)
    return () => window.removeEventListener('android-back', onBack)
  }, [open])

  if (!open) {
    return null
  }

  const status =
    phase === 'muted'
      ? t('callMuted')
      : phase === 'thinking'
        ? t('callThinking')
        : phase === 'speaking'
          ? t('callSpeaking')
          : t('callListening')

  return (
    <div
      className={styles.page}
      data-phase={phase}
      data-speaking={level > 0.06 ? 'true' : undefined}
      ref={page}
    >
      <header className={styles.header}>
        <div className={styles.headerText}>
          <h1>{title || t('untitledChat')}</h1>
          <span>{t('callInProgress', { time: formatDuration(seconds) })}</span>
        </div>
        <button
          type="button"
          className={styles.headerButton}
          aria-label={t('callVoiceTitle')}
          onClick={() => setSheet(true)}
        >
          <IconSwitchOutline20 />
        </button>
      </header>

      <div className={styles.stage} aria-hidden="true">
        {mode === 'voice' ? (
          <div className={styles.orb} style={{ ['--level' as string]: level }}>
            <span className={styles.orbSheen} />
            <span className={styles.orbCore} />
          </div>
        ) : null}
      </div>

      {phase === 'speaking' ? (
        <button type="button" className={styles.interrupt} onClick={interrupt}>
          <span className={styles.interruptMark} aria-hidden="true" />
          {t('callInterrupt')}
        </button>
      ) : null}

      <div className={styles.status} aria-live="polite">
        {phase === 'listening' ? (
          <span className={styles.waves} aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
        ) : null}
        {status}
      </div>

      <div className={styles.controls}>
        <button
          type="button"
          className={clsx(styles.round, styles.mic)}
          data-off={phase === 'muted' ? 'true' : undefined}
          aria-label={phase === 'muted' ? t('callUnmute') : t('callMute')}
          aria-pressed={phase === 'muted'}
          onClick={toggleMute}
        >
          <MicrophoneIcon muted={phase === 'muted'} />
        </button>

        {mode === 'voice' ? (
          <button
            type="button"
            className={clsx(styles.round, styles.hangup)}
            aria-label={t('callEnd')}
            onClick={() => {
              endCall()
              closeVoiceCall()
            }}
          >
            <IconPhoneOffOutline />
          </button>
        ) : (
          <button
            type="button"
            className={styles.inlineOrb}
            aria-label={t('callTextMode')}
            onClick={() => setMode('voice')}
          >
            <span className={styles.orb} style={{ ['--level' as string]: level }}>
              <span className={styles.orbSheen} />
              <span className={styles.orbCore} />
            </span>
          </button>
        )}

        {mode === 'voice' ? (
          <button
            type="button"
            className={clsx(styles.round, styles.textMode)}
            aria-label={t('callTextMode')}
            onClick={() => setMode('text')}
          >
            <span aria-hidden="true">文</span>
          </button>
        ) : (
          <button
            type="button"
            className={clsx(styles.round, styles.hangup)}
            aria-label={t('callEnd')}
            onClick={() => {
              endCall()
              closeVoiceCall()
            }}
          >
            <IconPhoneOffOutline />
          </button>
        )}
      </div>

      {mode === 'text' ? (
        <button
          type="button"
          className={styles.chevron}
          aria-label={t('callVoiceMode')}
          onClick={() => setMode('voice')}
        >
          <IconChevronDownOutline14 />
        </button>
      ) : null}

      <p className={styles.caveat}>{t('androidContentCaveat')}</p>
      {sheet ? <CallSettingsSheet onClose={() => setSheet(false)} /> : null}
    </div>
  )
}
