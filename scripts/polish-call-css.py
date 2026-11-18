"""Rewrite the voice-call orb and button styles into a glass / iridescent look."""

from pathlib import Path

CSS = Path('src/components/call/VoiceCallScreen.module.css')
text = CSS.read_text(encoding='utf-8')

START = text.index('.orb {')
END = text.index('.status {')
NEW_ORB = '''.orb {
  --level: 0;
  position: relative;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  isolation: isolate;
  /* 三层叠加：中心高光、外圈色散、边缘透明，让它像一团光而不是一个球 */
  background:
    radial-gradient(
      58% 54% at 38% 30%,
      rgb(255 255 255 / 96%) 0%,
      rgb(232 240 255 / 78%) 24%,
      rgb(160 186 255 / 52%) 46%,
      rgb(104 138 240 / 30%) 64%,
      rgb(70 100 210 / 14%) 80%,
      transparent 100%
    ),
    conic-gradient(
      from 200deg at 50% 50%,
      rgb(120 160 255 / 30%),
      rgb(186 148 255 / 24%),
      rgb(118 206 255 / 26%),
      rgb(88 126 236 / 30%),
      rgb(120 160 255 / 30%)
    );
  filter: blur(0.3px) saturate(118%);
  transform: scale(calc(1 + var(--level) * 0.075));
  transition:
    transform var(--motion-metric),
    width var(--motion-sheet),
    height var(--motion-sheet),
    opacity 320ms ease-out,
    filter 320ms ease-out;
  animation: orb-breathe 4.6s ease-in-out infinite;
}

/* 外发光：单独一层做模糊，才有"光渗进背景"的感觉 */
.orb::before {
  content: '';
  position: absolute;
  inset: -46%;
  z-index: -1;
  border-radius: 50%;
  background: radial-gradient(
    closest-side,
    rgb(112 152 255 / 52%),
    rgb(112 152 255 / 16%) 52%,
    transparent 74%
  );
  filter: blur(24px);
  animation: orb-halo 4.6s ease-in-out infinite;
}

/* 玻璃边缘：上沿一道高光、下沿一层冷色反光 */
.orb::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  box-shadow:
    inset 0 2px 12px rgb(255 255 255 / 55%),
    inset 0 -18px 34px rgb(44 74 190 / 30%),
    inset 2px 0 10px rgb(190 210 255 / 26%);
  mix-blend-mode: screen;
  pointer-events: none;
}

/* 内侧高光，偏左上，制造折射感 */
.orbCore {
  position: absolute;
  top: 14%;
  left: 18%;
  width: 46%;
  height: 42%;
  border-radius: 50%;
  background: radial-gradient(closest-side, rgb(255 255 255 / 90%), transparent 78%);
  filter: blur(9px);
  pointer-events: none;
}

.page[data-phase='thinking'] .orb {
  animation-duration: 1.5s;
}

.page[data-phase='speaking'] .orb {
  animation-duration: 2.2s;
  filter: blur(0.3px) saturate(132%) brightness(1.07);
}

/* 静音时光球收成一个小球，和官方一致 */
.page[data-phase='muted'] .orb {
  width: 48px;
  height: 48px;
  opacity: 0.45;
  animation: none;
  transform: none;
  filter: blur(0.6px) saturate(60%);
}

.page[data-phase='muted'] .orb::before {
  inset: -60%;
  animation: none;
  opacity: 0.5;
}

.page[data-phase='muted'] .orbCore {
  width: 52%;
  height: 48%;
  top: 16%;
  left: 16%;
}

@keyframes orb-breathe {
  0%,
  100% {
    transform: scale(calc(1 + var(--level) * 0.075));
  }

  50% {
    transform: scale(calc(1.045 + var(--level) * 0.075));
  }
}

@keyframes orb-halo {
  0%,
  100% {
    opacity: 0.82;
    transform: scale(1);
  }

  50% {
    opacity: 1;
    transform: scale(1.08);
  }
}

'''

text = text[:START] + NEW_ORB + text[END:]

BTN_START = text.index('.round {')
BTN_END = text.index('.caveat {')
NEW_BTN = '''.round {
  position: relative;
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border: 1px solid rgb(255 255 255 / 16%);
  border-radius: 50%;
  /* 液态玻璃：半透明渐变 + 背景模糊 + 上沿高光 */
  background:
    linear-gradient(158deg, rgb(255 255 255 / 20%), rgb(255 255 255 / 6%) 52%, rgb(255 255 255 / 12%)),
    rgb(20 22 28 / 32%);
  backdrop-filter: blur(22px) saturate(165%);
  color: rgb(248 249 252 / 94%);
  font-size: 19px;
  cursor: pointer;
  box-shadow:
    0 12px 30px rgb(0 0 0 / 42%),
    inset 0 1px 0 rgb(255 255 255 / 34%),
    inset 0 -10px 22px rgb(255 255 255 / 5%);
  transition:
    transform var(--motion-press),
    background-color 180ms ease-out,
    box-shadow 180ms ease-out;

  &:active {
    transform: scale(0.9);
    box-shadow:
      0 6px 16px rgb(0 0 0 / 46%),
      inset 0 1px 0 rgb(255 255 255 / 26%),
      inset 0 -8px 18px rgb(255 255 255 / 4%);
  }
}

/* 顶部一道细高光弧，玻璃的"反光边" */
.round::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 50%;
  width: 54%;
  height: 34%;
  border-radius: 50%;
  transform: translateX(-50%);
  background: linear-gradient(180deg, rgb(255 255 255 / 46%), transparent 78%);
  filter: blur(4px);
  pointer-events: none;
}

.mic[data-off='true'] {
  background:
    linear-gradient(158deg, rgb(255 255 255 / 26%), rgb(255 255 255 / 10%) 52%, rgb(255 255 255 / 16%)),
    rgb(255 255 255 / 8%);
}

/* 挂断：红色玻璃胶囊 */
.hangup {
  width: 74px;
  height: 54px;
  border-radius: 27px;
  border-color: rgb(255 170 170 / 38%);
  background:
    linear-gradient(158deg, rgb(255 140 140 / 96%), rgb(226 52 58 / 92%) 58%, rgb(198 32 40 / 94%)),
    rgb(255 80 84 / 70%);
  color: #fff;
  backdrop-filter: blur(18px) saturate(150%);
  box-shadow:
    0 14px 34px rgb(255 56 60 / 34%),
    inset 0 1px 0 rgb(255 255 255 / 44%),
    inset 0 -10px 20px rgb(140 0 10 / 26%);

  &:active {
    background:
      linear-gradient(158deg, rgb(240 120 120 / 96%), rgb(208 44 50 / 92%) 58%, rgb(180 26 34 / 94%)),
      rgb(240 70 74 / 70%);
  }
}

.hangup::after {
  width: 46%;
  height: 30%;
  background: linear-gradient(180deg, rgb(255 255 255 / 40%), transparent 80%);
}

'''

text = text[:BTN_START] + NEW_BTN + text[BTN_END:]

# 底部再加一层渐晕，避免大面积纯黑
text = text.replace(
    '''  color: #f2f3f5;
  animation: call-enter var(--motion-reveal);''',
    '''  color: #f2f3f5;
  animation: call-enter var(--motion-reveal);

  /* 顶部与底部各一层极淡的渐晕，避免大块纯黑显得廉价 */
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
      radial-gradient(90% 52% at 50% 0%, rgb(70 100 220 / 12%), transparent 68%),
      radial-gradient(80% 40% at 50% 100%, rgb(60 90 200 / 10%), transparent 70%);
  }''',
)

CSS.write_text(text, encoding='utf-8')
print('rewrote orb + buttons, size', len(text))
