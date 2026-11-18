"""Search should cover assistant text too, and load sessions in parallel."""

from pathlib import Path

PAGE = Path('src/components/search/SessionSearchPage.tsx')
page = PAGE.read_text(encoding='utf-8')

page = page.replace(
    "import { loadSession } from '../../services/chat/db.js'",
    "import { loadSession } from '../../services/chat/db.js'\nimport { buildReplyView } from '../../services/chat/format.js'",
    1,
)

page = page.replace(
    """        const messageHit = session?.messages.find((message) =>
          userText(message).toLocaleLowerCase().includes(term)
        )""",
    """        const messageHit = session?.messages.find((message) =>
          messageText(message).toLocaleLowerCase().includes(term)
        )""",
    1,
)
page = page.replace(
    "        const text = messageHit ? userText(messageHit) : ''",
    "        const text = messageHit ? messageText(messageHit) : ''",
    1,
)

page = page.replace(
    """type MessageLike = { role: string } & Record<string, unknown>

/** 只有用户消息带纯文本 content；助手消息是分段结构 */
const userText = (message: MessageLike) =>
  message.role === 'user' && typeof message.content === 'string' ? (message.content as string) : ''""",
    """type MessageLike = { role: string } & Record<string, unknown>

/** 用户消息是纯文本，助手消息要过一遍回复视图才能拿到正文 */
const messageText = (message: MessageLike) => {
  if (message.role === 'user' && typeof message.content === 'string') {
    return message.content
  }
  try {
    return buildReplyView(message as never, false).answer?.text ?? ''
  } catch {
    return ''
  }
}""",
    1,
)

# 并行加载，快很多
page = page.replace(
    """      const found: Hit[] = []
      for (const summary of recent) {
        if (!active) {
          return
        }
        const titleHit = summary.title.toLocaleLowerCase().includes(term)
        const session =
          useChatStore.getState().sessionCache[summary.id] ??
          (await loadSession(summary.id).catch(() => undefined))""",
    """      const found: Hit[] = []
      const loaded = await Promise.all(
        recent.map(
          async (summary) =>
            useChatStore.getState().sessionCache[summary.id] ??
            (await loadSession(summary.id).catch(() => undefined))
        )
      )
      for (const [index, summary] of recent.entries()) {
        if (!active) {
          return
        }
        const titleHit = summary.title.toLocaleLowerCase().includes(term)
        const session = loaded[index]""",
    1,
)

page = page.replace("    }, 180)", "    }, 120)", 1)
PAGE.write_text(page, encoding='utf-8')
print('search covers assistant text and loads in parallel')
