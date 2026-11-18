"""订阅跳转目标本身，保证同一会话内再次搜索也能精确跳转；并做一次位置校正。"""

import re
from pathlib import Path

LIST = Path('src/components/messages/MessageList.tsx')
tsx = LIST.read_text(encoding='utf-8')

# 1) 订阅目标（之前只读 getState()，deps 不变时不会重跑）
if 'const scrollTarget = useScrollTarget' not in tsx:
    anchor = '  useLayoutEffect(() => {\n    const anchor = restoreScrollRef.current'
    tsx = tsx.replace(
        anchor,
        '  // 订阅跳转目标：同一会话里再次搜索时，deps 可能不变，必须靠它触发\n'
        '  const scrollTarget = useScrollTarget((state) => state.target)\n\n' + anchor,
        1,
    )

# 2) 用订阅到的值，并加一次校正
OLD = """    // 搜索点击后：精确滚到命中的那条消息并高亮一下
    const target = useScrollTarget.getState().target
    if (target && target.sessionId === session.id && scroll) {
      const node = scroll.querySelector<HTMLElement>(
        `[data-message-id="${CSS.escape(target.messageId)}"]`
      )
      if (node) {
        clearScrollTarget()
        stickyRef.current = false
        // scrollIntoView 在嵌套滚动容器里会去滚祖先，这里自己算偏移
        const box = scroll.getBoundingClientRect()
        const rect = node.getBoundingClientRect()
        const centered = scroll.scrollTop + (rect.top - box.top) - box.height / 2 + rect.height / 2
        const top = Math.max(0, Math.min(scroll.scrollHeight - scroll.clientHeight, centered))
        scroll.scrollTo({ top, behavior: 'smooth' })
        scrollTopRef.current = top
        node.classList.add(styles.flash)
        window.setTimeout(() => node.classList.remove(styles.flash), 1400)
        return
      }
    }"""
NEW = """    // 搜索点击后：精确滚到命中的那条消息并高亮一下
    if (scrollTarget && scrollTarget.sessionId === session.id && scroll) {
      const node = scroll.querySelector<HTMLElement>(
        `[data-message-id="${CSS.escape(scrollTarget.messageId)}"]`
      )
      if (node) {
        clearScrollTarget()
        stickyRef.current = false
        const place = () => {
          const box = scroll.getBoundingClientRect()
          const rect = node.getBoundingClientRect()
          const centered = scroll.scrollTop + (rect.top - box.top) - box.height / 2 + rect.height / 2
          const top = Math.max(0, Math.min(scroll.scrollHeight - scroll.clientHeight, centered))
          scroll.scrollTo({ top, behavior: 'smooth' })
          scrollTopRef.current = top
          return top
        }
        const target = place()
        node.classList.add(styles.flash)
        window.setTimeout(() => node.classList.remove(styles.flash), 1400)
        // 图片/代码块可能延迟撑开高度，稍后再校正一次（用户没自己滚才校正）
        window.setTimeout(() => {
          if (Math.abs(scroll.scrollTop - target) < 4) {
            place()
          }
        }, 260)
        return
      }
    }"""
assert OLD in tsx, 'scroll branch not found'
tsx = tsx.replace(OLD, NEW, 1)

# 3) deps 加上目标
tsx = tsx.replace(
    '}, [session.id, lastMessageId, scrollToBottom])',
    '}, [session.id, lastMessageId, scrollToBottom, scrollTarget])',
    1,
)
LIST.write_text(tsx, encoding='utf-8')
print('scroll target subscription + correction applied')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', r'versionCode = 52', gradle), encoding='utf-8')
print('versionCode 52')
