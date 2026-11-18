"""Show a tappable 'speak or tap to interrupt' pill while the AI is talking."""

import re
from pathlib import Path

# 1) 会话 hook 暴露 interrupt
CALL = Path('src/components/call/useCallSession.ts')
call = CALL.read_text(encoding='utf-8')
call = call.replace(
    """  return { phase, level, seconds, toggleMute, endCall: stopAll }""",
    """  /** 打断当前朗读，立刻回到收音 */
  const interrupt = useCallback(() => {
    playback.current?.abort()
    playback.current = null
    setPhase('listening')
    setRound((value) => value + 1)
  }, [])

  return { phase, level, seconds, toggleMute, interrupt, endCall: stopAll }""",
    1,
)
CALL.write_text(call, encoding='utf-8')
print('interrupt exposed')

# 2) 通话页：说话时显示打断按钮
PAGE = Path('src/components/call/VoiceCallScreen.tsx')
page = PAGE.read_text(encoding='utf-8')
page = page.replace(
    '  const { phase, level, seconds, toggleMute, endCall } = useCallSession(open)',
    '  const { phase, level, seconds, toggleMute, interrupt, endCall } = useCallSession(open)',
    1,
)
OLD_STATUS = """      <div className={styles.status} aria-live="polite">"""
NEW_STATUS = """      {phase === 'speaking' ? (
        <button type="button" className={styles.interrupt} onClick={interrupt}>
          <span className={styles.interruptMark} aria-hidden="true" />
          {t('callInterrupt')}
        </button>
      ) : null}

      <div className={styles.status} aria-live="polite">"""
assert OLD_STATUS in page
page = page.replace(OLD_STATUS, NEW_STATUS, 1)
PAGE.write_text(page, encoding='utf-8')
print('interrupt button rendered')

# 3) 文案
for path, line in (
    (Path('src/i18n/zh.ts'), "  callInterrupt: '说话或轻触打断',\n"),
    (Path('src/i18n/en.ts'), "  callInterrupt: 'Speak or tap to interrupt',\n"),
):
    text = path.read_text(encoding='utf-8')
    if 'callInterrupt' not in text:
        text = text.replace('  callListening:', line + '  callListening:', 1)
        path.write_text(text, encoding='utf-8')
        print('i18n', path)

# 4) 样式
CSS = Path('src/components/call/VoiceCallScreen.module.css')
css = CSS.read_text(encoding='utf-8')
if '.interrupt {' not in css:
    css += """
/* 朗读中的打断提示：官方是圆角胶囊 + 一个小方块图标 */
.interrupt {
  display: flex;
  align-items: center;
  gap: 10px;
  align-self: center;
  margin: 0 auto 18px;
  padding: 12px 22px;
  border: 1px solid rgb(255 255 255 / 10%);
  border-radius: 999px;
  background: rgb(255 255 255 / 7%);
  color: rgb(242 243 245 / 82%);
  font: inherit;
  font-size: 15px;
  cursor: pointer;
  transition: transform var(--motion-press), background-color 160ms ease-out;

  &:active {
    transform: scale(0.96);
    background: rgb(255 255 255 / 13%);
  }
}

.interruptMark {
  width: 13px;
  height: 13px;
  border-radius: 4px;
  background: rgb(242 243 245 / 72%);
}
"""
    CSS.write_text(css, encoding='utf-8')
    print('interrupt styles added')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 21', gradle), encoding='utf-8')
print('versionCode 21')
