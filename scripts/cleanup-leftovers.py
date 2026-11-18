"""清掉残留：MobileHeader 的调试点击块、Sider 的旧图标导入。"""

import re
from pathlib import Path

HEADER = Path('src/components/session/MobileHeader.tsx')
header = HEADER.read_text(encoding='utf-8')

start = header.find('          <div\n        className={styles.title}\n        onClick={() => {')
if start < 0:
    start = header.find('        onClick={() => {\n          taps.current += 1')
    start = header.rfind('<div', 0, start) if start > 0 else -1

if start >= 0:
    close = header.find('>{title}</div>', start)
    if close > 0:
        header = header[:start] + '          <div className={styles.title}>{title}</div>' + header[close + len('>{title}</div>'):]
        HEADER.write_text(header, encoding='utf-8')
        print('debug tap block removed')
    else:
        print('close tag not found')
else:
    print('tap block not found')

# 兜底：删掉残留的 taps 引用
header = HEADER.read_text(encoding='utf-8')
if 'taps.current' in header:
    header = re.sub(r"\n\s*onClick=\{\(\) => \{\n[\s\S]*?\n\s*\}\}", '', header, count=1)
    HEADER.write_text(header, encoding='utf-8')
    print('onClick removed by regex')

SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')
sider = sider.replace(
    "import { IconCollapseSidebar16, IconPinOutline20 } from '../base/appIcons.js'",
    "import { IconPinOutline20 } from '../base/appIcons.js'",
)
SIDER.write_text(sider, encoding='utf-8')
print('sider icon import cleaned')
