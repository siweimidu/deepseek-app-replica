"""跳转后多帧校正，直到位置稳定；用户一碰就停止校正。"""

import re
from pathlib import Path

LIST = Path('src/components/messages/MessageList.tsx')
tsx = LIST.read_text(encoding='utf-8')

start = tsx.index('    // 搜索点击后：精确滚到命中的那条消息并高亮一下')
end = tsx.index('    stickyRef.current = true\n    scrollToBottom()', start)
NEW = """    // 搜索点击后：精确滚到命中的那条消息并高亮一下
    if (scrollTarget && scrollTarget.sessionId === session.id && scroll) {
      const node = scroll.querySelector<HTMLElement>(
        `[data-message-id="${CSS.escape(scrollTarget.messageId)}"]`
      )
      if (node) {
        clearScrollTarget()
        stickyRef.current = false
        node.classList.add(styles.flash)
        window.setTimeout(() => node.classList.remove(styles.flash), 1600)

        // 布局可能持续变化（图片、代码块撑高），多帧校正直到稳定；用户一碰就停
        let cancelled = false
        const stop = () => {
          cancelled = true
        }
        scroll.addEventListener('pointerdown', stop, { once: true, passive: true })
        scroll.addEventListener('wheel', stop, { once: true, passive: true })
        scroll.addEventListener('touchstart', stop, { once: true, passive: true })

        const align = (smooth: boolean) => {
          if (cancelled || !node.isConnected) {
            return
          }
          const box = scroll.getBoundingClientRect()
          const rect = node.getBoundingClientRect()
          const centered =
            scroll.scrollTop + (rect.top - box.top) - box.height / 2 + rect.height / 2
          const top = Math.max(0, Math.min(scroll.scrollHeight - scroll.clientHeight, centered))
          if (Math.abs(scroll.scrollTop - top) < 2) {
            return
          }
          scroll.scrollTo({ top, behavior: smooth ? 'smooth' : 'auto' })
          scrollTopRef.current = top
        }

        align(true)
        window.setTimeout(() => align(false), 120)
        window.setTimeout(() => align(false), 360)
        window.setTimeout(() => align(false), 720)
        return
      }
    }
"""
tsx = tsx[:start] + NEW + tsx[end:]
LIST.write_text(tsx, encoding='utf-8')
print('multi-pass jump alignment applied')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 52', gradle), encoding='utf-8')
print('versionCode 52')
