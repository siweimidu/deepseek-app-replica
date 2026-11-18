"""Motion tokens per the skill package: spring-default for the drawer, softer tail for the card."""

import re
from pathlib import Path

MOTION = Path('src/app/motion.css')
motion = MOTION.read_text(encoding='utf-8')

# spring-default (stiffness 200 / damping 22) 采样成 linear()：约 1.7% 过冲，320ms 收尾
SPRING = (
    "linear(0, 0.173 15%, 0.471 31%, 0.764 50%, 0.931 69%, 0.995 84%, 1.017 92%, 1.005 97%, 1)"
)
CARD = (
    "linear(0, 0.132 15%, 0.392 31%, 0.708 50%, 0.912 69%, 0.995 84%, 1.014 92%, 1.004 97%, 1)"
)

motion = re.sub(r"--motion-drawer:\s*\n?\s*[^;]+;", f"--motion-drawer: 320ms {SPRING};", motion)
if '--motion-card' not in motion:
    motion = motion.replace(
        f"--motion-drawer: 320ms {SPRING};",
        f"--motion-drawer: 320ms {SPRING};\n  /* 卡片比抽屉慢一档：形成层次，看起来是抽屉把页面推开 */\n  --motion-card: 360ms {CARD};",
        1,
    )
MOTION.write_text(motion, encoding='utf-8')
print('drawer/card spring tokens set')

APP = Path('src/app/App.module.css')
app = APP.read_text(encoding='utf-8')
app = app.replace(
    "  transition: transform var(--drawer-transition);\n}\n\n[data-android] .frame[data-drawer-open='true'] .main {",
    "  transition: transform var(--drawer-transition);\n}\n\n[data-android] .frame[data-drawer-open='true'] .main {",
)
# 卡片的过渡曲线用 --motion-card（比抽屉慢一档）
if '--motion-card' in motion:
    app = app.replace(
        """[data-android] .main {
  z-index: 1;""",
        """[data-android] .frame {
  --drawer-transition: var(--motion-drawer);
}

[data-android] .main {
  z-index: 1;""",
        1,
    )
    app = re.sub(
        r"(\.main \{[^}]*?)transition: transform var\(--drawer-transition\);",
        r"\1transition: transform var(--motion-card);",
        app,
        count=1,
        flags=re.S,
    )
APP.write_text(app, encoding='utf-8')
print('card uses --motion-card')

# 抽屉不再常驻 will-change（由 JS 在手势期间临时挂）
SIDER = Path('src/components/sider/Sider.module.css')
sider = SIDER.read_text(encoding='utf-8')
sider = sider.replace(
    "  /* 单独一层交给合成器，滑动期间不触发页面重绘 */\n  will-change: transform;\n",
    "",
)
SIDER.write_text(sider, encoding='utf-8')
print('permanent will-change removed')

GLOBAL = Path('src/app/global.css')
glob = GLOBAL.read_text(encoding='utf-8')
if 'prefers-reduced-motion' not in glob:
    glob += """
/* 无障碍：偏好减少动效时，位移直接到位 */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
"""
    GLOBAL.write_text(glob, encoding='utf-8')
    print('reduced-motion fallback added')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 43', gradle), encoding='utf-8')
print('versionCode 43')
