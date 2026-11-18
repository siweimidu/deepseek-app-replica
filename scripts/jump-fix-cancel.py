"""去掉"清空目标导致 effect 重跑取消定时器"的问题。"""

import re
from pathlib import Path

LIST = Path('src/components/messages/MessageList.tsx')
tsx = LIST.read_text(encoding='utf-8')

start = tsx.index('    // 搜索点击后：精确滚到命中的那条消息并高亮')
end = tsx.index('    stickyRef.current = true\n    scrollToBottom()', start)
NEW = """    // 搜索点击后：精确滚到命中的那条消息并高亮
    if (scrollTarget && scrollTarget.sessionId === session.id && scroll) {
      const scroller = scroll
      const messageId = scrollTarget.messageId
      stickyRef.current = false
      // 立即消费掉目标；下面的定时器不依赖 effect 生命周期，不会被重跑取消
      clearScrollTarget()

      const find = () =>
        scroller.querySelector<HTMLElement>(`[data-message-id="${CSS.escape(messageId)}"]`)

      const align = () => {
        if (!scroller.isConnected) {
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

      // 消息可能分批渲染：等节点出现后多帧校正
      ;[0, 80, 200, 400, 700, 1100, 1600].forEach((delay) => window.setTimeout(align, delay))
    }
"""
tsx = tsx[:start] + NEW + tsx[end:]
LIST.write_text(tsx, encoding='utf-8')
print('jump no longer self-cancels')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 61', gradle), encoding='utf-8')
print('versionCode 61')
