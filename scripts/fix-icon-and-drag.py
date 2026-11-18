"""Align the call icon with the other header icons, sync drawer drag with the card, trim compositing cost."""

from pathlib import Path
import re

# ---------- 1) 图标：与相邻两个同尺寸同描边 ----------
ICONS = Path('src/components/base/appIcons.tsx')
icons = ICONS.read_text(encoding='utf-8')
OLD_PHONE = """/** 通话入口：听筒 */
export const IconPhoneOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <path
      {...line}
      d="M6.6 3.4h2.2l1.5 3.6-1.8 1.2a11.4 11.4 0 0 0 5.3 5.3l1.2-1.8 3.6 1.5v2.2a2.2 2.2 0 0 1-2.4 2.2A16.6 16.6 0 0 1 4.4 5.8a2.2 2.2 0 0 1 2.2-2.4Z"
    />
  </svg>
)"""
NEW_PHONE = """/** 通话入口：听筒。尺寸/描边与顶部其它图标保持一致（22 / 1.9 / 圆角端点） */
export const IconPhoneOutline20 = () => (
  <svg
    width="22"
    height="22"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.9"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M6.4 3.2h2.5l1.6 3.9-2 1.3a11.8 11.8 0 0 0 5.1 5.1l1.3-2 3.9 1.6v2.5a2.3 2.3 0 0 1-2.5 2.3A17.2 17.2 0 0 1 4.1 5.7 2.3 2.3 0 0 1 6.4 3.2Z" />
  </svg>
)"""
assert OLD_PHONE in icons, 'phone icon not found'
ICONS.write_text(icons.replace(OLD_PHONE, NEW_PHONE, 1), encoding='utf-8')
print('phone icon matched to siblings')

# 去掉只给通话按钮加的额外位移，间距交给 header 统一 gap
HEADER = Path('src/components/session/MobileHeader.module.css')
header = HEADER.read_text(encoding='utf-8')
header = header.replace("""
/* 语音通话入口与静音按钮之间留一点间距 */
.call {
  margin-left: 2px;
}
""", '')
HEADER.write_text(header, encoding='utf-8')
print('call margin removed')

# ---------- 2) 拖动时抽屉与卡片同步 ----------
SIDER_CSS = Path('src/components/sider/Sider.module.css')
sider_css = SIDER_CSS.read_text(encoding='utf-8')
sider_css = sider_css.replace(
    """  transform: translateX(
    calc(
      (var(--drawer-progress) - 1 + var(--back-progress, 0)) * 100% +
        var(--drawer-drag, 0px)
    )
  );""",
    """  /* 位置完全由 --drawer-progress 决定，拖动时改它就同时带动卡片 */
  transform: translateX(calc((var(--drawer-progress) - 1 + var(--back-progress, 0)) * 100%));""",
)
SIDER_CSS.write_text(sider_css, encoding='utf-8')
print('drawer transform uses progress only:', '--drawer-drag' not in sider_css)

APP_CSS = Path('src/app/App.module.css')
app_css = APP_CSS.read_text(encoding='utf-8')
app_css = app_css.replace(
    """  transform: translateX(var(--drawer-edge));
  border-radius: 26px;""",
    """  /* 跟着同一个 progress 值走，拖动时和抽屉一起动 */
  transform: translateX(calc(var(--drawer-edge) * var(--drawer-progress)));
  border-radius: 26px;""",
)
# 去掉常驻 will-change（整屏图层常驻反而增加显存与合成压力），并在关闭时不做裁剪
app_css = app_css.replace("""[data-android] .frame[data-drawer-open='true'] .main {
  will-change: transform;
}""", '')
app_css = app_css.replace("""  padding-top: var(--android-status-inset, 0px);
  overflow: hidden;
  background: var(--dsw-alias-bg-base);""", """  padding-top: var(--android-status-inset, 0px);
  background: var(--dsw-alias-bg-base);""")
app_css = app_css.replace("""  transform: translateX(calc(var(--drawer-edge) * var(--drawer-progress)));
  border-radius: 26px;""", """  transform: translateX(calc(var(--drawer-edge) * var(--drawer-progress)));
  border-radius: 26px;
  overflow: hidden;""")
APP_CSS.write_text(app_css, encoding='utf-8')
print('card follows progress; will-change removed')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 18', gradle), encoding='utf-8')
print('versionCode 18')
