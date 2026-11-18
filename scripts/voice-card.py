"""Voice sheet: gradient preview per voice, swipe anywhere on the block, official copy."""

import re
from pathlib import Path

TSX = Path('src/components/call/VoiceCallScreen.tsx')
text = TSX.read_text(encoding='utf-8')

# 1) 文案：官方是「俏皮甜美 / 低沉浑厚」
text = text.replace(
    "{ id: 'stella' as const, label: t('settingsTtsVoiceStella'), description: t('callVoiceClear') }",
    "{ id: 'stella' as const, label: t('settingsTtsVoiceStella'), description: t('callVoiceSweet') }",
    1,
)

# 2) 把拖动手势从预览图挪到「预览 + 名称 + 描述 + 圆点」整块上
OLD_PREVIEW = text[text.index('        <div\n          className={styles.voicePreview}'):text.index('        <h2 className={styles.sectionTitle}>')]
NEW_BLOCK = """        <div
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
"""
text = text[: text.index('        <div\n          className={styles.voicePreview}')] + NEW_BLOCK + text[text.index('        <h2 className={styles.sectionTitle}>'):]
TSX.write_text(text, encoding='utf-8')
print('voice stage wired')

# 3) 样式：两种音色各自的渐变预览
CSS = Path('src/components/call/VoiceCallScreen.module.css')
css = CSS.read_text(encoding='utf-8')
css = css.replace(
    """.voicePreview {
  /* 横向留给切换音色，纵向留给弹层滚动 */
  touch-action: pan-y;
  transition: transform 240ms cubic-bezier(0.2, 0.72, 0.25, 1);
  user-select: none;
  height: 104px;""",
    """.voiceStage {
  display: flex;
  flex-direction: column;
  align-items: center;
  /* 横向留给切换音色，纵向留给弹层滚动 */
  touch-action: pan-y;
  user-select: none;
  transition: transform 240ms cubic-bezier(0.2, 0.72, 0.25, 1);
}

.voicePreview {
  height: 104px;""",
)
css = css.replace(
    """  margin: 18px 0 14px;
  border-radius: 22px;""",
    """  width: 200px;
  margin: 18px 0 14px;
  border-radius: 44px;""",
)
css = css.replace(
    """  background:
    radial-gradient(120% 140% at 24% 20%, #9fb4d8 0%, #5f7391 40%, #33404f 74%, #1d242c 100%);""",
    """  /* 海星：暖橘奶油；暗潮：冷蓝雾 */
  background: radial-gradient(120% 140% at 30% 24%, #ffe9c4 0%, #ffd79a 38%, #f6b96a 72%, #e79a4a 100%);
  transition: background 260ms ease-out;""",
)
css = css.replace(
    """.voiceName {""",
    """.voicePreview[data-voice='tide'] {
  background: radial-gradient(120% 140% at 26% 22%, #dfe9f2 0%, #b9cfe0 40%, #7f9bb2 74%, #56707f 100%);
}

.voiceName {""",
)
CSS.write_text(css, encoding='utf-8')
print('voice gradients added')

for path, line in (
    (Path('src/i18n/zh.ts'), "  callVoiceSweet: '俏皮甜美',\n"),
    (Path('src/i18n/en.ts'), "  callVoiceSweet: 'Playful and sweet',\n"),
):
    text = path.read_text(encoding='utf-8')
    if 'callVoiceSweet' not in text:
        text = text.replace('  callVoiceClear:', line + '  callVoiceClear:', 1)
        path.write_text(text, encoding='utf-8')
        print('i18n', path)

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 25', gradle), encoding='utf-8')
print('versionCode 25')
