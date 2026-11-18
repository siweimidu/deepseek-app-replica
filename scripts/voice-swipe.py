"""Let the voice card be swiped left/right to switch tone, like the official sheet."""

import re
from pathlib import Path

TSX = Path('src/components/call/VoiceCallScreen.tsx')
text = TSX.read_text(encoding='utf-8')

# 1) 弹层里加滑动状态
OLD_STATE = """  const active = tones.findIndex((tone) => tone.id === ttsVoice)
"""
NEW_STATE = """  const active = tones.findIndex((tone) => tone.id === ttsVoice)
  const [dragX, setDragX] = useState(0)
  const startX = useRef<number | null>(null)

  const switchTo = (step: number) => {
    const next = (Math.max(0, active) + step + tones.length) % tones.length
    setTtsVoice(tones[next].id)
  }
"""
assert OLD_STATE in text, 'active line not found'
text = text.replace(OLD_STATE, NEW_STATE, 1)

# 2) 预览卡接上拖动
OLD_PREVIEW = """        <div className={styles.voicePreview} aria-hidden="true" />"""
NEW_PREVIEW = """        <div
          className={styles.voicePreview}
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
            if (Math.abs(moved) > 36) {
              switchTo(moved < 0 ? 1 : -1)
            }
          }}
          onPointerCancel={() => {
            startX.current = null
            setDragX(0)
          }}
        />"""
assert OLD_PREVIEW in text, 'preview not found'
text = text.replace(OLD_PREVIEW, NEW_PREVIEW, 1)

TSX.write_text(text, encoding='utf-8')
print('voice card swipe wired')

CSS = Path('src/components/call/VoiceCallScreen.module.css')
css = CSS.read_text(encoding='utf-8')
if '.voicePreview {' in css and 'touch-action: pan-y' not in css:
    css = css.replace(
        """.voicePreview {
  height: 104px;""",
        """.voicePreview {
  /* 横向留给切换音色，纵向留给弹层滚动 */
  touch-action: pan-y;
  transition: transform 240ms cubic-bezier(0.2, 0.72, 0.25, 1);
  user-select: none;
  height: 104px;""",
        1,
    )
    CSS.write_text(css, encoding='utf-8')
    print('preview swipe styles added')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 20', gradle), encoding='utf-8')
print('versionCode 20')
