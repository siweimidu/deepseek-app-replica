"""用 rect 计算偏移，并从当前行往上找真正的滚动容器。"""

import re
from pathlib import Path

SIDER = Path('src/components/sider/Sider.tsx')
tsx = SIDER.read_text(encoding='utf-8')

start = tsx.find('  // 打开侧边栏时把当前会话滚到列表顶部')
end = tsx.find('  const groups = useMemo(() => {', start)
assert start >= 0 and end > start, 'effect block not found'

NEW = '''  // 打开侧边栏时把当前会话滚到列表顶部（只改滚动位置，顺序完全不变）
  useEffect(() => {
    if (!activeId) {
      return
    }
    const frame = requestAnimationFrame(() => {
      const row = document.querySelector<HTMLElement>(
        `[data-session-id="${CSS.escape(activeId)}"]`
      )
      if (!row) {
        return
      }
      // 从行往上找真正的滚动容器（不依赖 ref 挂在哪里）
      let scroller: HTMLElement | null = row.parentElement
      while (scroller) {
        const style = getComputedStyle(scroller)
        const scrollable =
          (style.overflowY === 'auto' || style.overflowY === 'scroll') &&
          scroller.scrollHeight > scroller.clientHeight + 4
        if (scrollable) {
          break
        }
        scroller = scroller.parentElement
      }
      if (!scroller) {
        return
      }
      const box = scroller.getBoundingClientRect()
      const rect = row.getBoundingClientRect()
      const delta = rect.top - box.top + scroller.scrollTop
      scroller.scrollTop = Math.max(0, Math.round(delta))
    })
    return () => cancelAnimationFrame(frame)
  }, [activeId, sessions.length])

'''
tsx = tsx[:start] + NEW + tsx[end:]
tsx = tsx.replace('  const listRef = useRef<HTMLDivElement>(null)\n', '')
tsx = tsx.replace("className={styles.list}\n          ref={listRef}", "className={styles.list}")
SIDER.write_text(tsx, encoding='utf-8')
print('scroll effect rewritten (rect-based, scroller auto-detected)')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 50', gradle), encoding='utf-8')
print('versionCode 50')
