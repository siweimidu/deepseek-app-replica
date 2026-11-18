"""通话页改成两种状态：语音（大球 + 三个圆钮）/ 文字（小球嵌进按钮排 + 展开箭头）。"""

from pathlib import Path

TSX = Path('src/components/call/VoiceCallScreen.tsx')
text = TSX.read_text(encoding='utf-8')

# 1) 增加 mode 状态
text = text.replace(
    "  const [sheet, setSheet] = useState(false)",
    "  const [sheet, setSheet] = useState(false)\n  const [mode, setMode] = useState<'voice' | 'text'>('voice')",
    1,
)
text = text.replace(
    "    if (!open) {\n      setSheet(false)\n      return\n    }",
    "    if (!open) {\n      setSheet(false)\n      setMode('voice')\n      return\n    }",
    1,
)

# 2) 舞台只在语音模式显示大球
OLD_STAGE = """      <div className={styles.stage}>
        <div
          className={styles.orb}
          style={{ ['--level' as string]: level }}
          data-level={level > 0.06 ? 'high' : 'low'}
          aria-hidden="true"
        >
          <span className={styles.orbSheen} />
          <span className={styles.orbCore} />
        </div>
      </div>"""
NEW_STAGE = """      <div className={styles.stage} aria-hidden="true">
        {mode === 'voice' ? (
          <div className={styles.orb} style={{ ['--level' as string]: level }}>
            <span className={styles.orbSheen} />
            <span className={styles.orbCore} />
          </div>
        ) : null}
      </div>"""
assert OLD_STAGE in text
text = text.replace(OLD_STAGE, NEW_STAGE, 1)

# 3) 底部按两种模式排列按钮
OLD_CONTROLS_START = text.index('      <div className={styles.controls}>')
OLD_CONTROLS_END = text.index('      <p className={styles.caveat}>')
NEW_CONTROLS = """      <div className={styles.controls}>
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
          <IconChevronUpOutline14 />
        </button>
      ) : null}

"""
text = text[:OLD_CONTROLS_START] + NEW_CONTROLS + text[OLD_CONTROLS_END:]

# 4) 内联的麦克风图标抽成小组件，两种模式共用
text = text.replace(
    "const formatDuration = (total: number) => {",
    """const MicrophoneIcon = ({ muted }: { muted: boolean }) => (
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

const formatDuration = (total: number) => {""",
    1,
)

# 5) 补 import
text = text.replace(
    "import { IconGlobeLanguageOutline14 } from '../base/icons.js'",
    "import { IconChevronUpOutline14, IconGlobeLanguageOutline14 } from '../base/icons.js'",
    1,
)

TSX.write_text(text, encoding='utf-8')
print('call screen: two modes wired')
