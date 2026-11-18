"""跳转要落到关键词所在的文字上，而不是整条消息。"""

import re
from pathlib import Path

# 1) 跳转目标带上关键词
STATE = Path('src/services/chat/scrollTarget.ts')
STATE.write_text("""import { create } from 'zustand'

/** 需要滚动定位到的消息 + 关键词（由搜索点击设置，消息列表消费） */
type Target = { sessionId: string; messageId: string; term: string } | null

export const useScrollTarget = create<{ target: Target }>(() => ({ target: null }))

export const requestScrollToMessage = (sessionId: string, messageId: string, term: string) =>
  useScrollTarget.setState({ target: { sessionId, messageId, term } })

export const clearScrollTarget = () => useScrollTarget.setState({ target: null })
""", encoding='utf-8')
print('scroll target now carries the term')

PAGE = Path('src/components/search/SessionSearchPage.tsx')
page = PAGE.read_text(encoding='utf-8')
page = page.replace(
    "      requestScrollToMessage(hit.sessionId, hit.messageId)",
    "      requestScrollToMessage(hit.sessionId, hit.messageId, query.trim())",
)
PAGE.write_text(page, encoding='utf-8')
print('search page passes the term')

# 2) 消息列表：定位到关键词文字
LIST = Path('src/components/messages/MessageList.tsx')
tsx = LIST.read_text(encoding='utf-8')

start = tsx.index('    // 搜索点击后：精确滚到命中的那条消息并高亮')
end = tsx.index('    stickyRef.current = true\n    scrollToBottom()', start)
NEW = """    // 搜索点击后：滚到关键词所在的**那段文字**，并把关键词标出来
    if (scrollTarget && scrollTarget.sessionId === session.id && scroll) {
      const scroller = scroll
      const { messageId, term } = scrollTarget
      stickyRef.current = false
      clearScrollTarget()

      /** 在消息里找到关键词对应的 Range（跨节点也能定位） */
      const findRange = (root: HTMLElement): Range | null => {
        if (!term) {
          return null
        }
        const needle = term.toLocaleLowerCase()
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
        const nodes: { node: Text; start: number }[] = []
        let text = ''
        let current: Node | null = walker.nextNode()
        while (current) {
          const textNode = current as Text
          nodes.push({ node: textNode, start: text.length })
          text += textNode.data
          current = walker.nextNode()
        }
        const index = text.toLocaleLowerCase().indexOf(needle)
        if (index < 0 || nodes.length === 0) {
          return null
        }
        const locate = (offset: number) => {
          for (let i = nodes.length - 1; i >= 0; i -= 1) {
            if (offset >= nodes[i].start) {
              return { node: nodes[i].node, offset: offset - nodes[i].start }
            }
          }
          return { node: nodes[0].node, offset: 0 }
        }
        const from = locate(index)
        const to = locate(index + needle.length)
        const range = document.createRange()
        try {
          range.setStart(from.node, Math.min(from.offset, from.node.data.length))
          range.setEnd(to.node, Math.min(to.offset, to.node.data.length))
        } catch {
          return null
        }
        return range
      }

      /** 用 CSS Highlight API 标出关键词（不支持就跳过，不影响定位） */
      const highlight = (range: Range) => {
        const api = (window as unknown as { CSS?: { highlights?: Map<string, unknown> }; Highlight?: unknown })
        if (!api.CSS?.highlights || !api.Highlight) {
          return
        }
        try {
          api.CSS.highlights.set('dsh-search-hit', new (api.Highlight as new (r: Range) => unknown)(range))
          window.setTimeout(() => api.CSS?.highlights?.delete('dsh-search-hit'), 2600)
        } catch {
          // 忽略
        }
      }

      const anchorRect = () => {
        const node = scroller.querySelector<HTMLElement>(
          `[data-message-id="${CSS.escape(messageId)}"]`
        )
        if (!node) {
          return null
        }
        const range = findRange(node)
        if (range) {
          highlight(range)
          const box = range.getBoundingClientRect()
          if (box.height > 0) {
            return { rect: box, node }
          }
        }
        return { rect: node.getBoundingClientRect(), node }
      }

      const align = () => {
        if (!scroller.isConnected) {
          return
        }
        const found = anchorRect()
        if (!found) {
          return
        }
        if (!found.node.classList.contains(styles.flash)) {
          found.node.classList.add(styles.flash)
          window.setTimeout(() => found.node.classList.remove(styles.flash), 2000)
        }
        const box = scroller.getBoundingClientRect()
        const { rect } = found
        // 让关键词落在视口中部偏上（1/3 处），确保它一定可见
        const desired = box.top + box.height * 0.32
        const top = scroller.scrollTop + (rect.top - desired)
        const max = scroller.scrollHeight - scroller.clientHeight
        const next = Math.max(0, Math.min(max, top))
        if (Math.abs(scroller.scrollTop - next) > 2) {
          scroller.scrollTo({ top: next, behavior: 'smooth' })
          scrollTopRef.current = next
        }
      }

      ;[0, 80, 200, 400, 700, 1100, 1600].forEach((delay) => window.setTimeout(align, delay))
    }
"""
tsx = tsx[:start] + NEW + tsx[end:]
LIST.write_text(tsx, encoding='utf-8')
print('jump now targets the keyword text')

# 3) 关键词高亮样式（::highlight 必须是全局选择器）
GLOBAL = Path('src/app/global.css')
glob = GLOBAL.read_text(encoding='utf-8')
if 'dsh-search-hit' not in glob:
    glob += """
/* 搜索跳转时标出命中的关键词 */
::highlight(dsh-search-hit) {
  background-color: rgb(77 107 254 / 32%);
  color: inherit;
}
"""
    GLOBAL.write_text(glob, encoding='utf-8')
    print('highlight style added')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 64', gradle), encoding='utf-8')
print('versionCode 64')
