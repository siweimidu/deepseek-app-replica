"""MessageList consumes the scroll target: jump to the matched message and flash it."""

import re
from pathlib import Path

LIST = Path('src/components/messages/MessageList.tsx')
list_tsx = LIST.read_text(encoding='utf-8')

# 1) 引入状态
if 'useScrollTarget' not in list_tsx:
    list_tsx = list_tsx.replace(
        "import { selectMessageVersion } from '../../services/chat/store.js'",
        "import { selectMessageVersion } from '../../services/chat/store.js'\nimport { clearScrollTarget, useScrollTarget } from '../../services/chat/scrollTarget.js'",
        1,
    )

# 2) 在原来的「切版本保持位置 / 否则滚到底」逻辑里插入搜索定位分支
OLD = """    stickyRef.current = true
    scrollToBottom()
  }, [session.id, lastMessageId, scrollToBottom])"""
NEW = """    // 搜索点击后：精确滚到命中的那条消息并高亮一下
    const target = useScrollTarget.getState().target
    if (target && target.sessionId === session.id && scroll) {
      const node = scroll.querySelector<HTMLElement>(
        `[data-message-id="${CSS.escape(target.messageId)}"]`
      )
      if (node) {
        clearScrollTarget()
        stickyRef.current = false
        node.scrollIntoView({ block: 'center', behavior: 'smooth' })
        node.classList.add(styles.flash)
        window.setTimeout(() => node.classList.remove(styles.flash), 1400)
        return
      }
    }
    stickyRef.current = true
    scrollToBottom()
  }, [session.id, lastMessageId, scrollToBottom])"""
assert OLD in list_tsx, 'scroll effect tail not found'
list_tsx = list_tsx.replace(OLD, NEW, 1)
LIST.write_text(list_tsx, encoding='utf-8')
print('message list consumes scroll target')

# 3) 高亮样式（用过渡淡出，不依赖 @keyframes）
CSS = Path('src/components/messages/MessageList.module.css')
css = CSS.read_text(encoding='utf-8')
if '.flash' not in css:
    css += """
/* 搜索命中的消息：短暂高亮，1.4s 内淡出 */
.flash {
  border-radius: 14px;
  background: color-mix(in srgb, #4d6bfe 14%, transparent);
  box-shadow: 0 0 0 2px color-mix(in srgb, #4d6bfe 55%, transparent);
  transition:
    background-color 500ms ease-out,
    box-shadow 500ms ease-out;
}
"""
    CSS.write_text(css, encoding='utf-8')
    print('flash style added')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 48', gradle), encoding='utf-8')
print('versionCode 48')
