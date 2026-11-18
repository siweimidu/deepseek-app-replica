"""滚动到选中会话时避开吸顶的分组标题，让它完整露在标题下方。"""

import re
from pathlib import Path

SIDER = Path('src/components/sider/Sider.tsx')
tsx = SIDER.read_text(encoding='utf-8')

# 1) 分组与标题加标记，便于计算吸顶高度
tsx = tsx.replace(
    '<div key={group.key} className={styles.section}>',
    '<div key={group.key} className={styles.section} data-session-group={group.key}>',
    1,
)
tsx = tsx.replace(
    '<div className={styles.sectionHeader}>{group.label}</div>',
    '<div className={styles.sectionHeader} data-session-header>\n                {group.label}\n              </div>',
    1,
)

# 2) 滚动计算减去吸顶标题高度
OLD = """      const box = scroller.getBoundingClientRect()
      const rect = row.getBoundingClientRect()
      const delta = rect.top - box.top + scroller.scrollTop
      scroller.scrollTop = Math.max(0, Math.round(delta))"""
NEW = """      const box = scroller.getBoundingClientRect()
      const rect = row.getBoundingClientRect()
      // 分组标题是 sticky 的，会把行的上沿盖住；滚动时让出这一段高度
      const section = row.closest('[data-session-group]')
      const header = section?.querySelector<HTMLElement>('[data-session-header]')
      const headerHeight = header ? Math.ceil(header.getBoundingClientRect().height) : 0
      const delta = rect.top - box.top + scroller.scrollTop - headerHeight
      scroller.scrollTop = Math.max(0, Math.round(delta))"""
assert OLD in tsx, 'scroll math not found'
tsx = tsx.replace(OLD, NEW, 1)
SIDER.write_text(tsx, encoding='utf-8')
print('sticky header offset applied')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 51', gradle), encoding='utf-8')
print('versionCode 51')
