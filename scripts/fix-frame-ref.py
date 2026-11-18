"""Reuse the existing frame ref instead of declaring a second one."""

import re
from pathlib import Path

APP = Path('src/app/App.tsx')
app = APP.read_text(encoding='utf-8')

app = app.replace(
    "  const frameRef = useRef<HTMLDivElement>(null)\n  useDrawerSwipe(frameRef)\n",
    "",
    1,
)
app = app.replace(
    "  const frameRef = useMobileViewport(isMobile)\n",
    "  const frameRef = useMobileViewport(isMobile)\n  useDrawerSwipe(frameRef)\n",
    1,
)
# 去掉重复的 ref 属性
app = app.replace(
    """      <div
        ref={frameRef}
        className={styles.frame}
      ref={frameRef}
        data-drawer-open={drawerOpen}""",
    """      <div
        ref={frameRef}
        className={styles.frame}
        data-drawer-open={drawerOpen}""",
    1,
)
if 'useRef' not in re.sub(r"import .*\n", '', app):
    app = app.replace("import { useEffect, useRef } from 'react'", "import { useEffect } from 'react'", 1)
APP.write_text(app, encoding='utf-8')
print('frame ref deduplicated')
