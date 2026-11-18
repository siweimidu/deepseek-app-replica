"""官方图标：两个空心圆，每个右边一条短横线（项目符号列表样式）。"""

import re
from pathlib import Path

ICONS = Path('src/components/base/appIcons.tsx')
icons = ICONS.read_text(encoding='utf-8')

NEW = '''/** 收起侧边栏：两个空心圆 + 右侧短横线（对齐官方图标） */
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
    <circle cx="8" cy="9" r="2.35" />
    <path d="M13.4 9h5" />
    <circle cx="8" cy="15" r="2.35" />
    <path d="M13.4 15h5" />
  </svg>
)
'''

pattern = re.compile(
    r"/\*\*[^*]*收起侧边栏[^*]*\*/\s*export const IconCollapseSidebar16 = \(\) => \([\s\S]*?\n\)\n",
    re.M,
)
assert pattern.search(icons), 'icon block not found'
icons = pattern.sub(NEW, icons, count=1)
ICONS.write_text(icons, encoding='utf-8')
print('icon redrawn: rings + dashes')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 56', gradle), encoding='utf-8')
print('versionCode 56')
