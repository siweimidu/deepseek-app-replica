"""加回搜索框右侧的「收起侧边栏」按钮。"""

import re
from pathlib import Path

# ---------- 1) 图标：两点 + 一竖 ----------
ICONS = Path('src/components/base/appIcons.tsx')
icons = ICONS.read_text(encoding='utf-8')
if 'IconCollapseSidebar16' not in icons:
    icons += """
/** 收起侧边栏：两个圆点 + 一条竖线 */
export const IconCollapseSidebar16 = () => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    aria-hidden="true"
  >
    <circle cx="8" cy="9.2" r="1.5" fill="currentColor" stroke="none" />
    <circle cx="8" cy="14.8" r="1.5" fill="currentColor" stroke="none" />
    <path d="M16 5.5v13" />
  </svg>
)
"""
    ICONS.write_text(icons, encoding='utf-8')
    print('collapse icon added')

# ---------- 2) 搜索行：输入框 + 按钮 ----------
SIDER = Path('src/components/sider/Sider.tsx')
tsx = SIDER.read_text(encoding='utf-8')

OLD = """        <label className={styles.search} onClick={() => openSessionSearch()}>
          <IconSearchOutline16 />
          <input
            type="search"
            placeholder={t('androidSearchChats')}
            aria-label={t('androidSearchChats')}
            value=""
            readOnly
            onFocus={() => openSessionSearch()}
          />
        </label>"""
NEW = """        <div className={styles.searchRow}>
          <label className={styles.search} onClick={() => openSessionSearch()}>
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
          <button
            type="button"
            className={styles.collapse}
            aria-label={t('collapseSider')}
            onClick={closeMobileSider}
          >
            <IconCollapseSidebar16 />
          </button>
        </div>"""
assert OLD in tsx, 'search label not found'
tsx = tsx.replace(OLD, NEW, 1)

if 'IconCollapseSidebar16' not in tsx:
    tsx = tsx.replace(
        "  IconPinOutline20,\n} from '../base/appIcons.js'",
        "  IconCollapseSidebar16,\n  IconPinOutline20,\n} from '../base/appIcons.js'",
        1,
    )
SIDER.write_text(tsx, encoding='utf-8')
print('collapse button wired')

# ---------- 3) 样式 ----------
CSS = Path('src/components/sider/Sider.module.css')
css = CSS.read_text(encoding='utf-8')
if '.searchRow' not in css:
    css += """
/* 搜索框 + 收起按钮一行 */
[data-android] .searchRow {
  display: flex;
  align-items: center;
  gap: 10px;
}

[data-android] .searchRow .search {
  flex: 1;
  min-width: 0;
}

[data-android] .collapse {
  display: grid;
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  place-items: center;
  padding: 0;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--dsw-alias-label-secondary);
  cursor: pointer;
  transition: transform var(--motion-press), background-color 150ms ease-out;

  &:active {
    transform: scale(0.92);
    background: var(--dsw-alias-bg-skeleton);
  }
}
"""
    CSS.write_text(css, encoding='utf-8')
    print('collapse button styled')

# 文案
for path, line in (
    (Path('src/i18n/zh.ts'), "  collapseSider: '收起侧边栏',\n"),
    (Path('src/i18n/en.ts'), "  collapseSider: 'Collapse sidebar',\n"),
):
    text = path.read_text(encoding='utf-8')
    if 'collapseSider' not in text:
        text = text.replace('  androidSearchChats:', line + '  androidSearchChats:', 1)
        path.write_text(text, encoding='utf-8')
        print('i18n', path.name)

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 53', gradle), encoding='utf-8')
print('versionCode 53')
