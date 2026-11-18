"""1) 横滑逻辑换成上游原版；2) 把「选择对话」按钮按上游放回列表右上角，图标用空心圆。"""

import re
import shutil
from pathlib import Path

ROOT = Path('.')

# ============ A. 横滑：恢复上游实现 ============
shutil.copyfile(ROOT / '.upstream/useAndroidDrawerGesture.ts', ROOT / 'src/components/sider/useAndroidDrawerGesture.ts')
print('upstream gesture restored')

APP = ROOT / 'src/app/App.tsx'
app = APP.read_text(encoding='utf-8')
app = app.replace(
    "import { useDrawerSwipe } from '../components/sider/useDrawerSwipe.js'",
    "import { useAndroidDrawerGesture } from '../components/sider/useAndroidDrawerGesture.js'",
)
app = app.replace("  useDrawerSwipe(frameRef)\n", "  const drawerGesture = useAndroidDrawerGesture()\n")
if 'drawerGesture' in app and '{...(' not in app:
    app = app.replace(
        "        data-drawer-open={drawerOpen}\n",
        "        data-drawer-open={drawerOpen}\n        {...(android && isMobile ? drawerGesture : {})}\n",
        1,
    )
# 去掉调试角标
app = app.replace("import { SwipeDebugBadge } from '../components/sider/SwipeDebugBadge.js'\n", '')
app = app.replace("      <SwipeDebugBadge />\n", '')
APP.write_text(app, encoding='utf-8')
print('App wired to upstream gesture; debug badge removed')

for dead in ['src/components/sider/useDrawerSwipe.ts', 'src/components/sider/SwipeDebugBadge.tsx', 'src/components/sider/SwipeDebugBadge.module.css']:
    p = ROOT / dead
    if p.exists():
        p.unlink()
        print('removed', dead)

# 头部标题连点 5 下的调试开关也去掉
HEADER = ROOT / 'src/components/session/MobileHeader.tsx'
header = HEADER.read_text(encoding='utf-8')
header = header.replace("import { toggleSwipeDebug } from '../sider/useDrawerSwipe.js'\n", '')
header = re.sub(
    r"\n      <div\n        className=\{styles\.title\}\n        onClick=\{\(\) => \{[\s\S]*?\n        \}\}\n      >",
    "\n      <div className={styles.title}>",
    header,
    count=1,
)
header = header.replace("  const taps = useRef(0)\n", '')
if 'useRef' not in header.replace("import { useRef } from 'react'\n", ''):
    header = header.replace("import { useRef } from 'react'\n", '')
HEADER.write_text(header, encoding='utf-8')
print('header debug toggle removed:', 'toggleSwipeDebug' not in header)

# 原生 dispatchTouchEvent 去掉（与上游一致）
JAVA = ROOT / 'android/app/src/main/java/com/deep/sleep/MainActivity.java'
java = JAVA.read_text(encoding='utf-8')
start = java.find('    @Override\n    public boolean dispatchTouchEvent')
if start >= 0:
    end = java.find('    /**', java.find('runOnUiThread(', start))
    java = java[:start] + java[end:] if end > start else java
    # 兜底：直接按方法边界裁掉
    if 'dispatchTouchEvent' in java:
        s2 = java.find('    @Override\n    public boolean dispatchTouchEvent')
        e2 = java.find('\n    }\n', java.find('return super.dispatchTouchEvent', s2)) + 7
        java = java[:s2] + java[e2:]
    java = java.replace('import android.view.MotionEvent;\n', '')
    java = re.sub(r'    // 横滑判定[^\n]*\n(    private float swipeDownX;|    private float swipeDownY;|    private boolean swipeTracking;|    private static final float SWIPE_DP[^\n]*|    private static final float SWIPE_RATIO[^\n]*)\n?', '', java)
    JAVA.write_text(java, encoding='utf-8')
print('native swipe removed:', 'dispatchTouchEvent' not in java)

# ============ B. 选择对话按钮 ============
SIDER = ROOT / 'src/components/sider/Sider.tsx'
sider = SIDER.read_text(encoding='utf-8')

# 1) 搜索行还原成只有输入框
OLD_ROW = re.search(
    r"        <div className=\{styles\.searchRow\}>[\s\S]*?</div>\n(?=      \) : \()",
    sider,
)
if OLD_ROW:
    sider = sider[: OLD_ROW.start()] + """        <label className={styles.search} onClick={() => openSessionSearch()}>
          <IconSearchOutline16 />
          <input
            type="search"
            placeholder={t('androidSearchChats')}
            aria-label={t('androidSearchChats')}
            value=""
            readOnly
            onFocus={() => openSessionSearch()}
          />
        </label>
""" + sider[OLD_ROW.end():]
    print('search row reverted to input only')

# 2) 列表右上角加「选择对话」按钮（上游位置 + 空心圆图标）
OLD_LIST = """      <div className={styles.listWrap}>
        <div className={styles.list}>"""
NEW_LIST = """      <div className={styles.listWrap}>
        {androidDrawer && !selecting ? (
          <IconButton
            className={styles.selectChats}
            size="m"
            icon={
              <svg
                width="18"
                height="18"
                viewBox="0 0 18 18"
                fill="none"
                stroke="currentColor"
                aria-hidden="true"
              >
                <circle cx="4" cy="5.2" r="2.1" strokeWidth="1.5" />
                <circle cx="4" cy="12.8" r="2.1" strokeWidth="1.5" />
                <path d="M8.6 5.2h6M8.6 12.8h6" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            }
            aria-label={t('androidSelectChats')}
            tooltip={t('androidSelectChats')}
            onClick={() => {
              setSelecting(true)
              setChecked(new Set(activeId ? [activeId] : []))
            }}
          />
        ) : null}
        <div className={styles.list}>"""
assert OLD_LIST in sider, 'listWrap anchor not found'
sider = sider.replace(OLD_LIST, NEW_LIST, 1)

# 3) 不再需要收起图标
sider = sider.replace("  IconCollapseSidebar16,\n", '')
SIDER.write_text(sider, encoding='utf-8')
print('select-chats button placed in list top-right')

# 4) CSS：去掉 searchRow/collapse，加 selectChats
CSS = ROOT / 'src/components/sider/Sider.module.css'
css = CSS.read_text(encoding='utf-8')
css = re.sub(r"/\* 搜索框 \+ 收起按钮一行 \*/[\s\S]*?\[data-android\] \.collapse \{[\s\S]*?\n\}\n", '', css)
if '.selectChats' not in css:
    css += """
/* 「选择对话」入口：贴在列表右上角（对齐官方位置） */
[data-android] .selectChats {
  position: absolute;
  top: 6px;
  right: 1px;
  z-index: 25;
}
"""
    CSS.write_text(css, encoding='utf-8')
    print('selectChats css added')

# 5) 图标组件不再需要
ICONS = ROOT / 'src/components/base/appIcons.tsx'
icons = ICONS.read_text(encoding='utf-8')
icons = re.sub(r"/\*\*[^*]*收起侧边栏[^*]*\*/\s*export const IconCollapseSidebar16 = \(\) => \([\s\S]*?\n\)\n", '', icons)
ICONS.write_text(icons, encoding='utf-8')
print('old collapse icon removed:', 'IconCollapseSidebar16' not in icons)

GRADLE = ROOT / 'android/app/build.gradle'
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 58', gradle), encoding='utf-8')
print('versionCode 58')
