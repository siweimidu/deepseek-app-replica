"""Replace the collapse icon block (it is the last export in the file)."""

import re
from pathlib import Path

ICONS = Path('src/components/base/appIcons.tsx')
icons = ICONS.read_text(encoding='utf-8')

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

pattern = re.compile(
    r"/\*\*[^*]*收起侧边栏[^*]*\*/\s*export const IconCollapseSidebar16 = \(\) => \([\s\S]*?\n\)\n",
    re.M,
)
if pattern.search(icons):
    icons = pattern.sub(NEW, icons, count=1)
    print('icon replaced via regex')
else:
    # 兜底：从 export 行开始截到文件末尾（它本来就是最后一个导出）
    start = icons.index('export const IconCollapseSidebar16')
    head = icons.rfind('/**', 0, start)
    icons = icons[: head if head >= 0 else start] + NEW
    print('icon replaced via tail slice')

ICONS.write_text(icons, encoding='utf-8')
print('bars icon present:', 'M4 9.1h16' in icons)

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 55', gradle), encoding='utf-8')
print('versionCode 55')
