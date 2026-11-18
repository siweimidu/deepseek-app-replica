"""Cut the real paint/layout hot spots instead of guessing."""

from pathlib import Path

# ---------- 1) 通话页：去掉 backdrop-filter 与逐帧模糊旋转 ----------
CALL = Path('src/components/call/VoiceCallScreen.module.css')
call = CALL.read_text(encoding='utf-8')

call = call.replace(
    """  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
""",
    """  /* 不用 backdrop-filter：Android WebView 每帧要回读背景，滑动时明显掉帧 */
""",
)

call = call.replace(
    """/* 缓慢旋转的内层云雾，让球体静止时也在流动 */
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
}""",
    """/* 静态云雾层：原来带 blur + 旋转，逐帧重绘很贵，改成静止的柔光 */
.orb > .orbSheen {
  position: absolute;
  inset: 4%;
  z-index: 0;
  border-radius: 50%;
  background: radial-gradient(
    60% 55% at 38% 32%,
    rgb(255 255 255 / 26%),
    rgb(255 255 255 / 8%) 46%,
    transparent 70%
  );
  pointer-events: none;
}""",
)

# 尺寸变化 → 纯 transform 缩放，避免逐帧 layout
call = call.replace(
    """  transition:
    transform var(--spring-pop),
    width var(--motion-sheet),
    height var(--motion-sheet),
    opacity 320ms ease-out,
    filter 320ms ease-out;""",
    """  transition:
    transform var(--spring-pop),
    opacity 240ms ease-out;""",
)
call = call.replace(
    """/* 静音时光球收成一个小球，和官方一致 */
.page[data-phase='muted'] .orb {
  width: 48px;
  height: 48px;
  opacity: 0.45;
  animation: none;
  transform: none;
  filter: blur(0.6px) saturate(60%);
}""",
    """/* 静音时光球收成一个小球：只缩放不做宽高动画，省掉整屏重排 */
.page[data-phase='muted'] .orb {
  opacity: 0.55;
  animation: none;
  transform: scale(0.33);
}""",
)
call = call.replace(
    """@keyframes orb-sheen {
  to {
    transform: rotate(360deg);
  }
}

""",
    '',
)
CALL.write_text(call, encoding='utf-8')
print('call css slimmed')

# ---------- 2) 导入状态条：去掉 backdrop-filter ----------
BAR = Path('src/components/base/ImportStatusBar.module.css')
bar = BAR.read_text(encoding='utf-8')
bar = bar.replace(
    """  background: color-mix(in srgb, var(--dsw-alias-bg-layer-3) 92%, transparent);
  backdrop-filter: blur(14px);
""",
    """  background: var(--dsw-alias-bg-layer-3);
""",
)
BAR.write_text(bar, encoding='utf-8')
print('status bar slimmed')

# ---------- 3) 对话卡片：大范围投影换成细边 + 小投影 ----------
APP = Path('src/app/App.module.css')
app = APP.read_text(encoding='utf-8')
app = app.replace(
    """[data-android] .frame[data-drawer-open='true'] .main {
  transform: translateX(var(--drawer-edge));
  border-radius: 26px;
  box-shadow:
    -14px 0 44px rgb(0 0 0 / 58%),
    inset 1px 0 0 rgb(255 255 255 / 7%);
}""",
    """[data-android] .frame[data-drawer-open='true'] .main {
  transform: translateX(var(--drawer-edge));
  border-radius: 26px;
  /* 44px 模糊阴影在整屏元素上很贵：改成一条细边 + 小范围投影 */
  box-shadow:
    0 0 0 1px rgb(255 255 255 / 7%),
    -6px 0 16px rgb(0 0 0 / 34%);
}""",
)
# will-change 只在真正要动的时候挂上
app = app.replace(
    """  transition: transform var(--drawer-transition);
  will-change: transform;
}""",
    """  transition: transform var(--drawer-transition);
}

[data-android] .frame[data-drawer-open='true'] .main {
  will-change: transform;
}""",
)
APP.write_text(app, encoding='utf-8')
print('card shadow slimmed')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
import re

GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 16', gradle), encoding='utf-8')
print('versionCode 16')
