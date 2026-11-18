"""把收起图标改成官方样式：长横线 + 短横线，左对齐。"""

import re
from pathlib import Path

ICONS = Path('src/components/base/appIcons.tsx')
icons = ICONS.read_text(encoding='utf-8')

start = icons.index('/** 收起侧边栏：两个圆点 + 一条竖线 */')
end = icons.index('/**', start + 10)
OLD = icons[start:end]
NEW = '''/** 收起侧边栏：上长下短两条横线，左对齐（对齐官方图标） */
export const IconCollapseSidebar16 = () => (
  <svg
    width="22"
    height="22"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    aria-hidden="true"
  >
    <path d="M4 9.1h16" />
    <path d="M4 15.3h8.6" />
  </svg>
)

'''
icons = icons[:start] + NEW + icons[end:]
ICONS.write_text(icons, encoding='utf-8')
print('collapse icon redrawn (two bars)')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 55', gradle), encoding='utf-8')
print('versionCode 55')
