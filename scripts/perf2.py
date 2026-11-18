"""Perf + tap-responsiveness pass."""

import re
from pathlib import Path

# ---------- 1) 预测性返回：挂载时无条件复位偏移（否则整页停在偏移位置，点击会跑偏） ----------
HOOK = Path('src/app/backGesture.ts')
hook = HOOK.read_text(encoding='utf-8')
OLD = """    const reset = () => {
      const element = ref.current
      if (!element) {
        return
      }
      element.removeAttribute('data-back')
      element.style.setProperty('--back-progress', '0')
    }"""
NEW = """    const reset = () => {
      const element = ref.current
      if (!element) {
        return
      }
      element.removeAttribute('data-back')
      element.style.setProperty('--back-progress', '0')
    }
    // 上一次手势如果被系统打断，偏移会留在元素上：先复位，避免整页偏着导致点击错位
    reset()"""
assert OLD in hook
HOOK.write_text(hook.replace(OLD, NEW, 1), encoding='utf-8')
print('predictive-back offset reset on mount')

# ---------- 2) 设置页：去掉入场动画与图层提升，点击即刻可用 ----------
SETTINGS = Path('src/components/settings/AndroidSettings.module.css')
css = SETTINGS.read_text(encoding='utf-8')
css = css.replace('  will-change: transform, opacity;\n', '')
css = css.replace('  animation: page-enter var(--motion-drawer);\n', '')
css = css.replace(
    """@keyframes page-enter {
  from {
    opacity: 0;
    transform: translateX(24%);
  }
}

""",
    '',
)
css = css.replace(
    """  position: fixed;
  z-index: 950;
  inset: 0;""",
    """  position: fixed;
  z-index: 950;
  inset: 0;
  /* 独立布局/绘制，避免设置页与下面聊天页互相触发重排 */
  contain: layout style paint;""",
)
SETTINGS.write_text(css, encoding='utf-8')
print('settings page: no entry animation, isolated')

# ---------- 3) 会话行：屏幕外的行不参与渲染 ----------
ITEM = Path('src/components/sider/SessionItem.module.css')
item = ITEM.read_text(encoding='utf-8')
if 'content-visibility' not in item:
    item = item.replace(
        """.item {
  position: relative;""",
        """.item {
  /* 长列表里屏幕外的行跳过渲染，滚动与打开抽屉都更轻 */
  content-visibility: auto;
  contain-intrinsic-size: 0 48px;
  position: relative;""",
        1,
    )
    ITEM.write_text(item, encoding='utf-8')
    print('session rows: content-visibility auto')

# ---------- 4) 剩下那个 40px 大阴影收小 ----------
APP = Path('src/app/App.module.css')
app = APP.read_text(encoding='utf-8')
app = re.sub(
    r'box-shadow:\s*-12px 0 40px rgb\(0 0 0 / 52%\);',
    'box-shadow: -6px 0 16px rgb(0 0 0 / 38%);',
    app,
)
APP.write_text(app, encoding='utf-8')
print('card shadow trimmed')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 22', gradle), encoding='utf-8')
print('versionCode 22')
