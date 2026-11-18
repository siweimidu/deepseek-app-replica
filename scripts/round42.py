"""Wire the native-listener hook, add a swipe debug badge, and put the app icon on the key screen."""

import re
from pathlib import Path

# ---------- 1) App：hook 不再返回属性 ----------
APP = Path('src/app/App.tsx')
app = APP.read_text(encoding='utf-8')
app = app.replace("  const drawerSwipe = useDrawerSwipe(frameRef)\n", "  useDrawerSwipe(frameRef)\n", 1)
app = app.split('\n')
app = [line for line in app if '{...drawerSwipe}' not in line]
app = '\n'.join(app)
APP.write_text(app, encoding='utf-8')
print('App no longer spreads handlers')

# ---------- 2) 调试角标组件 + 标题连点 5 次开关 ----------
BADGE = Path('src/components/sider/SwipeDebugBadge.tsx')
BADGE.write_text("""import { toggleSwipeDebug, useSwipeDebug } from './useDrawerSwipe.js'
import styles from './SwipeDebugBadge.module.css'

/** 手势调试角标：标题连点 5 次开关。出问题时能看出断在哪一环。 */
export const SwipeDebugBadge = () => {
  const { visible, down, move, toggle, last } = useSwipeDebug()
  if (!visible) {
    return null
  }
  return (
    <button type="button" className={styles.badge} onClick={toggleSwipeDebug}>
      down {down} · move {move} · toggle {toggle} · {last || '—'}
    </button>
  )
}
""", encoding='utf-8')

BADGE_CSS = Path('src/components/sider/SwipeDebugBadge.module.css')
BADGE_CSS.write_text(""".badge {
  position: fixed;
  z-index: 2000;
  bottom: 8px;
  left: 8px;
  padding: 4px 8px;
  border: 0;
  border-radius: 8px;
  background: rgb(255 80 80 / 85%);
  color: #fff;
  font: 11px/1.4 ui-monospace, monospace;
}
""", encoding='utf-8')
print('debug badge created')

HEADER = Path('src/components/session/MobileHeader.tsx')
header = HEADER.read_text(encoding='utf-8')
if 'toggleSwipeDebug' not in header:
    header = header.replace(
        "import { useTranslate } from '../../i18n/index.js'",
        "import { useTranslate } from '../../i18n/index.js'\nimport { toggleSwipeDebug } from '../sider/useDrawerSwipe.js'",
        1,
    )
    # 标题连点 5 次切换调试角标
    header = header.replace(
        """      <div className={styles.title}>""",
        """      <div
        className={styles.title}
        onClick={() => {
          taps.current += 1
          window.setTimeout(() => {
            taps.current = 0
          }, 900)
          if (taps.current >= 5) {
            taps.current = 0
            toggleSwipeDebug()
          }
        }}
      >""",
        1,
    )
    header = header.replace(
        "  const t = useTranslate()",
        "  const t = useTranslate()\n  const taps = useRef(0)",
        1,
    )
    HEADER.write_text(header, encoding='utf-8')
    print('header title toggles debug badge')

# App 里挂上角标
APP2 = Path('src/app/App.tsx')
app2 = APP2.read_text(encoding='utf-8')
if 'SwipeDebugBadge' not in app2:
    app2 = app2.replace(
        "import { ImportStatusBar } from '../components/base/ImportStatusBar.js'",
        "import { ImportStatusBar } from '../components/base/ImportStatusBar.js'\nimport { SwipeDebugBadge } from '../components/sider/SwipeDebugBadge.js'",
        1,
    )
    app2 = app2.replace("      <ImportStatusBar />", "      <SwipeDebugBadge />\n      <ImportStatusBar />", 1)
    APP2.write_text(app2, encoding='utf-8')
    print('badge mounted')

# ---------- 3) API Key 页换成应用图标 ----------
KEY = Path('src/components/settings/ApiKeyScreen.tsx')
key = KEY.read_text(encoding='utf-8')
key = key.replace(
    "import whale from '../../assets/deepseek-whale.svg'",
    "import appIcon from '../../assets/deepsleep-avatar.jpg'",
    1,
)
key = key.replace('<img className={styles.whale} src={whale} alt="" />', '<img className={styles.whale} src={appIcon} alt="" />', 1)
KEY.write_text(key, encoding='utf-8')
print('key screen uses app icon')

KEY_CSS = Path('src/components/settings/ApiKeyScreen.module.css')
css = KEY_CSS.read_text(encoding='utf-8')
css = re.sub(r'(\.whale \{[^}]*?)width: 52px;', r'\1width: 64px;\n  height: 64px;\n  border-radius: 18px;\n  object-fit: cover;', css, count=1)
KEY_CSS.write_text(css, encoding='utf-8')
print('key screen icon sized')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 42', gradle), encoding='utf-8')
print('versionCode 42')
