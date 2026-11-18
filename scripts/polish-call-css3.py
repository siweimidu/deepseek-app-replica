"""Match the official call screen: soft rimmed sphere + charcoal round buttons."""

from pathlib import Path

CSS = Path('src/components/call/VoiceCallScreen.module.css')
text = CSS.read_text(encoding='utf-8')

ORB_START = text.index('.orb {')
ORB_END = text.index('.status {')
NEW_ORB = """.orb {
  --level: 0;
  position: relative;
  width: 150px;
  height: 150px;
  border-radius: 50%;
  isolation: isolate;
  /* 官方是一颗带白边的柔光球：内部是灰蓝云雾，边缘一圈亮白 */
  background:
    radial-gradient(58% 50% at 34% 25%, rgb(255 255 255 / 82%), transparent 62%),
    radial-gradient(52% 46% at 63% 74%, rgb(255 255 255 / 62%), transparent 66%),
    radial-gradient(
      118% 118% at 50% 44%,
      #d9e2ee 0%,
      #c6d3e3 38%,
      #a3b3ca 62%,
      #7b8da6 82%,
      #56657c 94%,
      #3f4c60 100%
    );
  box-shadow:
    /* 白边环 + 内侧一圈柔光 */
    inset 0 0 0 2.5px rgb(255 255 255 / 86%),
    inset 0 0 20px 2px rgb(255 255 255 / 30%),
    inset 0 -22px 40px rgb(54 72 108 / 42%),
    /* 外发光 */
    0 0 58px 16px rgb(126 156 214 / 34%);
  filter: blur(0.2px) saturate(108%);
  /* 音量直接驱动尺寸，弹簧曲线让"说话"有弹性 */
  transform: scale(calc(1 + var(--level) * 0.2));
  transition:
    transform var(--spring-pop),
    width var(--motion-sheet),
    height var(--motion-sheet),
    opacity 320ms ease-out,
    filter 320ms ease-out;
  animation: orb-idle 5.2s ease-in-out infinite;
}

/* 缓慢旋转的内层云雾，让球体静止时也在流动 */
.orb > .orbSheen {
  position: absolute;
  inset: 4%;
  z-index: 0;
  border-radius: 50%;
  background: conic-gradient(
    from 0deg,
    rgb(255 255 255 / 0%),
    rgb(255 255 255 / 22%),
    rgb(180 200 230 / 0%),
    rgb(255 255 255 / 16%),
    rgb(255 255 255 / 0%)
  );
  filter: blur(12px);
  animation: orb-sheen 11s linear infinite;
  pointer-events: none;
}

/* 外发光：单独一层模糊，才有光渗进背景的感觉 */
.orb::before {
  content: '';
  position: absolute;
  inset: -52%;
  z-index: -1;
  border-radius: 50%;
  background: radial-gradient(
    closest-side,
    rgb(126 156 214 / 42%),
    rgb(126 156 214 / 14%) 54%,
    transparent 76%
  );
  filter: blur(26px);
  animation: orb-halo 5.2s ease-in-out infinite;
}

/* 边缘的玻璃反光：上沿更亮 */
.orb::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  box-shadow:
    inset 0 3px 10px rgb(255 255 255 / 62%),
    inset 0 -8px 18px rgb(70 92 130 / 26%);
  mix-blend-mode: screen;
  pointer-events: none;
}

/* 内侧高光，偏左上 */
.orbCore {
  position: absolute;
  top: 16%;
  left: 20%;
  width: 44%;
  height: 40%;
  border-radius: 50%;
  background: radial-gradient(closest-side, rgb(255 255 255 / 72%), transparent 76%);
  filter: blur(10px);
  pointer-events: none;
}

/* 检测到人声：光环更亮，配合弹簧缩放看得出来 */
.page[data-speaking='true'] .orb::before {
  opacity: 1;
  filter: blur(32px);
}

.page[data-speaking='true'] .orbCore {
  filter: blur(13px);
}

.page[data-phase='thinking'] .orb {
  animation-duration: 1.6s;
}

.page[data-phase='speaking'] .orb {
  animation-duration: 2.4s;
  filter: blur(0.2px) saturate(116%) brightness(1.04);
}

/* 静音时光球收成一个小球，和官方一致 */
.page[data-phase='muted'] .orb {
  width: 54px;
  height: 54px;
  opacity: 0.72;
  animation: none;
  transform: none;
  filter: blur(0.4px) saturate(70%);
}

.page[data-phase='muted'] .orb::before {
  inset: -70%;
  animation: none;
  opacity: 0.45;
}

.page[data-phase='muted'] .orbCore {
  width: 50%;
  height: 46%;
  top: 18%;
  left: 18%;
}

@keyframes orb-idle {
  0%,
  100% {
    filter: blur(0.2px) saturate(108%) brightness(1);
  }

  50% {
    filter: blur(0.2px) saturate(112%) brightness(1.045);
  }
}

@keyframes orb-halo {
  0%,
  100% {
    opacity: 0.8;
    transform: scale(1);
  }

  50% {
    opacity: 1;
    transform: scale(1.06);
  }
}

@keyframes orb-sheen {
  to {
    transform: rotate(360deg);
  }
}

"""

text = text[:ORB_START] + NEW_ORB + text[ORB_END:]

BTN_START = text.index('.controls {')
BTN_END = text.index('.caveat {')
NEW_BTN = """.controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-shrink: 0;
  padding: 22px 0 10px;
}

/* 官方的按钮是深炭灰圆钮 + 一圈极细亮边，不是玻璃 */
.round {
  position: relative;
  display: grid;
  place-items: center;
  width: 74px;
  height: 74px;
  border: 1px solid rgb(255 255 255 / 7%);
  border-radius: 50%;
  background: #2a2c31;
  color: rgb(238 240 244 / 94%);
  font-size: 21px;
  cursor: pointer;
  transition:
    transform var(--motion-press),
    background-color 160ms ease-out;

  &:active {
    transform: scale(0.93);
    background: #34363c;
  }
}

.mic[data-off='true'] {
  background: #36383e;
}

/* 挂断同样是深色圆钮，只有图标是红的 */
.hangup {
  color: #ff5a52;

  &:active {
    background: #3a2a2c;
  }
}

.textMode span {
  font-size: 22px;
  font-weight: 500;
}

"""
text = text[:BTN_START] + NEW_BTN + text[BTN_END:]

CSS.write_text(text, encoding='utf-8')
print('matched official style', len(text))
