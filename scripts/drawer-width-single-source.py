"""Single pixel source for drawer width so drawer and card can never desync."""

import re
from pathlib import Path

# 1) 删掉遗留的 appVersion（版本行已移除）
SETTINGS = Path('src/components/settings/AndroidSettings.tsx')
text = SETTINGS.read_text(encoding='utf-8')
text = re.sub(
    r"const appVersion = [\s\S]*?\)\?\.content \?\? ''\n",
    '',
    text,
)
SETTINGS.write_text(text, encoding='utf-8')
print('appVersion removed:', 'appVersion' not in text)

# 2) 抽屉宽度写入像素变量，卡片用同一个变量
SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')
anchor = """  const releaseDrag = () => {"""
addition = """  /** 抽屉宽度只由这里算一次，抽屉与卡片共用同一个像素值 */
  const syncWidth = () => {
    const element = drawer.current
    const frame = element?.parentElement
    if (!element || !frame) {
      return
    }
    frame.style.setProperty('--drawer-width', `${element.getBoundingClientRect().width}px`)
  }

  const releaseDrag = () => {"""
assert anchor in sider
if 'syncWidth' not in sider:
    sider = sider.replace(anchor, addition, 1)
    sider = sider.replace(
        """  useEffect(() => {
    if (drawer.current) {
      drawer.current.inert = !open
    }
  }, [open])""",
        """  useEffect(() => {
    if (drawer.current) {
      drawer.current.inert = !open
    }
    if (open) {
      syncWidth()
    }
  }, [open])""",
        1,
    )
    SIDER.write_text(sider, encoding='utf-8')
    print('syncWidth wired')

SIDER_CSS = Path('src/components/sider/Sider.module.css')
css = SIDER_CSS.read_text(encoding='utf-8')
css = css.replace('  width: var(--drawer-edge);', '  width: var(--drawer-width, var(--drawer-edge));')
SIDER_CSS.write_text(css, encoding='utf-8')
print('drawer width uses --drawer-width')

APP = Path('src/app/App.module.css')
app = APP.read_text(encoding='utf-8')
app = app.replace(
    '  transform: translateX(calc(var(--drawer-edge) * var(--drawer-progress)));',
    '  transform: translateX(calc(var(--drawer-width, var(--drawer-edge)) * var(--drawer-progress)));',
)
APP.write_text(app, encoding='utf-8')
print('card translate uses --drawer-width')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 19', gradle), encoding='utf-8')
print('versionCode 19')
