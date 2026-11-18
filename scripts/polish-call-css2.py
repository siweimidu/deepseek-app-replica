"""把通话页的按钮拉回官方的哑光质感，光球改成会呼吸、跟音量弹性变化。"""

from pathlib import Path

CSS = Path('src/components/call/VoiceCallScreen.module.css')
text = CSS.read_text(encoding='utf-8')

# ---- 光球：动画与弹性 ----
text = text.replace(
    """  filter: blur(0.3px) saturate(118%);
  transform: scale(calc(1 + var(--level) * 0.075));
  transition:
    transform var(--motion-metric),
    width var(--motion-sheet),
    height var(--motion-sheet),
    opacity 320ms ease-out,
    filter 320ms ease-out;
  animation: orb-breathe 4.6s ease-in-out infinite;
}""",
    """  filter: blur(0.3px) saturate(118%);
  /* 音量直接驱动尺寸，用弹簧曲线过渡 → 说话时会有弹性的鼓动 */
  transform: scale(calc(1 + var(--level) * 0.22));
  transition:
    transform var(--spring-pop),
    width var(--motion-sheet),
    height var(--motion-sheet),
    opacity 320ms ease-out,
    filter 320ms ease-out;
}""",
    1,
)

# 让色散层缓慢旋转：静止时也有"活着"的感觉
text = text.replace(
    """/* 外发光：单独一层做模糊，才有"光渗进背景"的感觉 */
.orb::before {""",
    """/* 呼吸放在伪元素上，避免和音量驱动的 transform 抢同一个属性 */
.orb {
  animation: orb-idle 5.2s ease-in-out infinite;
}

/* 缓慢旋转的色散，静止时也像一团活的光 */
.orb > .orbSheen {
  position: absolute;
  inset: -6%;
  z-index: 0;
  border-radius: 50%;
  background: conic-gradient(
    from 0deg,
    rgb(150 185 255 / 0%),
    rgb(190 165 255 / 26%),
    rgb(140 220 255 / 0%),
    rgb(170 195 255 / 22%),
    rgb(150 185 255 / 0%)
  );
  filter: blur(10px);
  animation: orb-sheen 9s linear infinite;
  pointer-events: none;
}

/* 外发光：单独一层做模糊，才有"光渗进背景"的感觉 */
.orb::before {""",
    1,
)

text = text.replace(
    """@keyframes orb-breathe {
  0%,
  100% {
    transform: scale(calc(1 + var(--level) * 0.075));
  }

  50% {
    transform: scale(calc(1.045 + var(--level) * 0.075));
  }
}""",
    """@keyframes orb-idle {
  0%,
  100% {
    filter: blur(0.3px) saturate(118%) brightness(1);
  }

  50% {
    filter: blur(0.3px) saturate(124%) brightness(1.06);
  }
}

@keyframes orb-sheen {
  to {
    transform: rotate(360deg);
  }
}""",
    1,
)

# 检测到说话时额外提亮一圈
text = text.replace(
    """.page[data-phase='thinking'] .orb {""",
    """/* 检测到人声：光环更亮，配合弹簧缩放看得出来 */
.page[data-speaking='true'] .orb::before {
  opacity: 1;
  filter: blur(30px);
}

.page[data-speaking='true'] .orbCore {
  filter: blur(12px);
}

.page[data-phase='thinking'] .orb {""",
    1,
)

# ---- 按钮：按官方改成克制的哑光半透明 ----
BTN_START = text.index('.round {')
BTN_END = text.index('.caveat {')
NEW_BTN = """.round {
  position: relative;
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border: 1px solid rgb(255 255 255 / 9%);
  border-radius: 50%;
  /* 官方是哑光半透明圆钮：一层很淡的白色、一圈细边、上沿一点内高光 */
  background: rgb(255 255 255 / 7%);
  color: rgb(244 245 248 / 92%);
  font-size: 19px;
  cursor: pointer;
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 7%);
  transition:
    transform var(--motion-press),
    background-color 180ms ease-out;

  &:active {
    transform: scale(0.92);
    background: rgb(255 255 255 / 13%);
  }
}

.mic[data-off='true'] {
  background: rgb(255 255 255 / 12%);
}

/* 挂断：红色，圆钮，图标是听筒朝下 */
.hangup {
  border-color: transparent;
  background: #f0453f;
  color: #fff;
  box-shadow: none;

  &:active {
    background: #d93a35;
  }
}

"""
text = text[:BTN_START] + NEW_BTN + text[BTN_END:]

CSS.write_text(text, encoding='utf-8')
print('polished call css', len(text))
