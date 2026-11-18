"""通话页按钮改成"液态玻璃"：背景模糊、渐变描边环、上沿镜面高光。"""

from pathlib import Path

CSS = Path('src/components/call/VoiceCallScreen.module.css')
text = CSS.read_text(encoding='utf-8')

BTN_START = text.index('.controls {')
BTN_END = text.index('.caveat {')
NEW = """.controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-shrink: 0;
  padding: 22px 0 10px;
}

/*
 * 液态玻璃：靠三件事撑起来——
 * ① 背景模糊，把光球的颜色"吸"进按钮里；② 一圈渐变描边（上亮下暗）；
 * ③ 上沿一道镜面高光 + 下沿内阴影，形成凸起的玻璃厚度。
 */
.round {
  position: relative;
  display: grid;
  place-items: center;
  width: 74px;
  height: 74px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background:
    radial-gradient(
      125% 105% at 50% -12%,
      rgb(255 255 255 / 24%),
      rgb(255 255 255 / 8%) 52%,
      rgb(255 255 255 / 4%) 100%
    ),
    rgb(20 24 32 / 34%);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  color: #f3f5f9;
  font-size: 21px;
  cursor: pointer;
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / 46%),
    inset 0 -1px 0 rgb(255 255 255 / 10%),
    inset 0 0 26px rgb(255 255 255 / 5%),
    0 10px 28px rgb(0 0 0 / 38%);
  transition:
    transform var(--motion-press),
    box-shadow 200ms ease-out,
    background-color 200ms ease-out;

  &:active {
    transform: scale(0.92);
    box-shadow:
      inset 0 1px 0 rgb(255 255 255 / 30%),
      inset 0 -1px 0 rgb(255 255 255 / 8%),
      0 5px 14px rgb(0 0 0 / 42%);
  }
}

/* 玻璃边缘：圆环的渐变描边，顶部最亮、底部收一点光 */
.round::before {
  content: '';
  position: absolute;
  inset: 0;
  padding: 1px;
  border-radius: inherit;
  background: linear-gradient(
    158deg,
    rgb(255 255 255 / 82%),
    rgb(255 255 255 / 20%) 30%,
    rgb(255 255 255 / 5%) 56%,
    rgb(255 255 255 / 34%)
  );
  -webkit-mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  mask-composite: exclude;
  pointer-events: none;
}

/* 上沿镜面反射 */
.round::after {
  content: '';
  position: absolute;
  top: 5%;
  left: 50%;
  width: 56%;
  height: 34%;
  transform: translateX(-50%);
  border-radius: 50%;
  background: linear-gradient(180deg, rgb(255 255 255 / 58%), transparent 82%);
  filter: blur(5px);
  opacity: 0.62;
  pointer-events: none;
}

/* 图标要压在玻璃层之上 */
.round > * {
  position: relative;
  z-index: 1;
}

.mic[data-off='true'] {
  background:
    radial-gradient(
      125% 105% at 50% -12%,
      rgb(255 255 255 / 34%),
      rgb(255 255 255 / 14%) 52%,
      rgb(255 255 255 / 8%) 100%
    ),
    rgb(30 34 44 / 40%);
}

/* 挂断：红色玻璃，同样的边缘与高光，只换色调 */
.hangup {
  color: #ff7a73;
  background:
    radial-gradient(
      125% 105% at 50% -12%,
      rgb(255 150 140 / 34%),
      rgb(255 92 80 / 16%) 54%,
      rgb(255 80 68 / 8%) 100%
    ),
    rgb(48 22 24 / 38%);
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / 44%),
    inset 0 -1px 0 rgb(255 150 140 / 16%),
    inset 0 0 26px rgb(255 96 84 / 12%),
    0 10px 30px rgb(255 56 48 / 26%),
    0 4px 12px rgb(0 0 0 / 34%);

  &:active {
    transform: scale(0.92);
    box-shadow:
      inset 0 1px 0 rgb(255 255 255 / 26%),
      0 5px 16px rgb(255 56 48 / 30%);
  }
}

.hangup::before {
  background: linear-gradient(
    158deg,
    rgb(255 198 192 / 88%),
    rgb(255 128 118 / 26%) 32%,
    rgb(255 96 84 / 8%) 58%,
    rgb(255 150 140 / 42%)
  );
}

.hangup::after {
  background: linear-gradient(180deg, rgb(255 210 205 / 52%), transparent 82%);
}

/* 文字模式里的小球是按钮，不要玻璃底 */
.inlineOrb {
  background: transparent;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  box-shadow: none;
}

.inlineOrb::before,
.inlineOrb::after {
  display: none;
}

"""
text = text[:BTN_START] + NEW + text[BTN_END:]
CSS.write_text(text, encoding='utf-8')
print('liquid glass buttons', len(text))
