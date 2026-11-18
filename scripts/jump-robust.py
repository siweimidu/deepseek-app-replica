"""加强搜索定位：轮询等待目标节点出现 + 更多次校正 + 更明显更久的高亮。"""

import re
from pathlib import Path

LIST = Path('src/components/messages/MessageList.tsx')
tsx = LIST.read_text(encoding='utf-8')

start = tsx.index('    // 搜索点击后：精确滚到命中的那条消息并高亮一下')
end = tsx.index('    stickyRef.current = true\n    scrollToBottom()', start)
NEW = """    // 搜索点击后：精确滚到命中的那条消息并高亮
    if (scrollTarget && scrollTarget.sessionId === session.id && scroll) {
      const scroller = scroll
      const messageId = scrollTarget.messageId
      stickyRef.current = false
      clearScrollTarget()

      let cancelled = false
      const stop = () => {
        cancelled = true
      }
      scroller.addEventListener('pointerdown', stop, { once: true, passive: true })
      scroller.addEventListener('wheel', stop, { once: true, passive: true })
      scroller.addEventListener('touchstart', stop, { once: true, passive: true })

      const find = () =>
        scroller.querySelector<HTMLElement>(`[data-message-id="${CSS.escape(messageId)}"]`)

      const align = () => {
        if (cancelled) {
          return
        }
        const node = find()
        if (!node) {
          return
        }
        if (!node.classList.contains(styles.flash)) {
          node.classList.add(styles.flash)
          window.setTimeout(() => node.classList.remove(styles.flash), 2000)
        }
        const box = scroller.getBoundingClientRect()
        const rect = node.getBoundingClientRect()
        const centered =
          scroller.scrollTop + (rect.top - box.top) - box.height / 2 + rect.height / 2
        const top = Math.max(0, Math.min(scroller.scrollHeight - scroller.clientHeight, centered))
        if (Math.abs(scroller.scrollTop - top) > 2) {
          scroller.scrollTo({ top, behavior: 'smooth' })
          scrollTopRef.current = top
        }
      }

      // 消息可能是分批渲染的：先等节点出现，再多帧校正位置
      const delays = [0, 80, 200, 400, 700, 1100, 1600]
      const timers = delays.map((delay) => window.setTimeout(align, delay))
      return () => {
        cancelled = true
        timers.forEach((id) => window.clearTimeout(id))
      }
    }
"""
tsx = tsx[:start] + NEW + tsx[end:]
LIST.write_text(tsx, encoding='utf-8')
print('search jump strengthened')

# 高亮更明显
CSS = Path('src/components/messages/MessageList.module.css')
css = CSS.read_text(encoding='utf-8')
css = re.sub(
    r"/\* 搜索命中的消息[\s\S]*?\.flash \{[\s\S]*?\n\}\n",
    """/* 搜索命中的消息：短暂高亮，2s 后淡出 */
.flash {
  border-radius: 14px;
  background: color-mix(in srgb, #4d6bfe 20%, transparent);
  box-shadow: 0 0 0 2px color-mix(in srgb, #4d6bfe 70%, transparent);
  transition:
    background-color 600ms ease-out,
    box-shadow 600ms ease-out;
}
""",
    css,
)
CSS.write_text(css, encoding='utf-8')
print('flash stronger')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 61', gradle), encoding='utf-8')
print('versionCode 61')
